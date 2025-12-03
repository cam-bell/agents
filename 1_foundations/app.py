from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import sqlite3
import re
import numpy as np

# RAG dependencies
try:
    import faiss
except ImportError:
    print("Installing faiss-cpu...")
    os.system("uv add faiss-cpu")
    import faiss

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("Installing rank-bm25...")
    os.system("uv add rank-bm25")
    from rank_bm25 import BM25Okapi


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Cameron Bell"
        
        # Load summary first
        with open("me/summary2.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        # Load LinkedIn profile
        self.linkedin = self._load_pdf("me/cameronbell2.pdf")
        
        # Load CVs using helper method (Option 3)
        self.cvs = {}
        self.cvs["ai_ml_engineer"] = self._load_pdf("me/cameronbell_cv.pdf")
        self.cvs["ml_engineer"] = self._load_pdf("me/cameron_bell_cv_machine_learning_engineer.pdf")
        
        # Combine for backward compatibility
        self.cv = "\n\n--- AI/ML Engineer CV ---\n\n" + self.cvs["ai_ml_engineer"]
        self.cv += "\n\n--- Machine Learning Engineer CV ---\n\n" + self.cvs["ml_engineer"]
        
        # Initialize RAG systems (needs documents loaded first)
        self._init_rag_systems()

        # Initialize SQLite database
        self.conn = sqlite3.connect('qa_database.db')
        self.cursor = self.conn.cursor()
        self._init_database()
    
    def _load_pdf(self, filepath):
        """Helper method to load PDF text"""
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    
    def _init_database(self):
        """Initialize Q&A database with sample data"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        sample_qa = [
            ("Where are you from?", "I'm from Southampton, Bermuda, but I've lived in England for 10 years and Madrid, Spain for a year during my MSc.", "background"),
            ("What's your educational background?", "I attended Ardingly College for boarding school, completed my International Baccalaureate, then went to University of Bristol for my MSc in Computer Science and Business Technology.", "education"),
            ("What are your hobbies?", "I love all foods, particularly trying new cuisine. I'm also a gym enthusiast and enjoy weights and calisthenics. I'm a big football fan too!", "personal"),
            ("Why did you move back to Bermuda?", "In 2022, I returned to Bermuda to be with my ageing grandfather and support my family.", "background"),
        ]
        
        for q, a, cat in sample_qa:
            self.cursor.execute("INSERT OR IGNORE INTO qa (question, answer, category) VALUES (?, ?, ?)", (q, a, cat))
        
        self.conn.commit()
    
    def search_qa(self, user_query, limit=3):
        """Search for relevant Q&A based on keyword matching"""
        keywords = re.findall(r'\b\w+\b', user_query.lower())
        keyword_pattern = '%' + '%'.join(keywords[:3]) + '%'
        
        self.cursor.execute('''
            SELECT question, answer, category 
            FROM qa 
            WHERE question LIKE ? OR answer LIKE ?
            LIMIT ?
        ''', (keyword_pattern, keyword_pattern, limit))
        
        results = self.cursor.fetchall()
        
        if results:
            context = "Relevant Q&A from knowledge base:\n"
            for q, a, cat in results:
                context += f"Q: {q}\nA: {a}\n\n"
            return context
        return None

    def _init_rag_systems(self):
        """Initialize RAG: chunk documents, build indexes"""
        # Chunk all documents
        self.doc_chunks = self._chunk_documents()
        
        # Build embeddings index (FAISS)
        self.faiss_index = self._build_faiss_index()
        
        # Build BM25 index
        self.bm25_index = self._build_bm25_index()

    def _chunk_documents(self, chunk_size=500, overlap=50):
        """Chunk all documents into smaller pieces for retrieval"""
        # Combine all text (summary, linkedin, and both CVs)
        all_text = self.summary + "\n\n" + self.linkedin + "\n\n"
        all_text += "--- AI/ML Engineer CV ---\n\n" + self.cvs["ai_ml_engineer"] + "\n\n"
        all_text += "--- Machine Learning Engineer CV ---\n\n" + self.cvs["ml_engineer"]
        
        # Split into chunks
        chunks = []
        start = 0
        while start < len(all_text):
            end = start + chunk_size
            chunk = all_text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks

    def _build_faiss_index(self):
        """Build embeddings index (FAISS)"""
        chunks = self.doc_chunks

        # Generate embeddings
        embeddings = []
        for chunk in chunks:
            response = self.openai.embeddings.create(
                model="text-embedding-3-small",
                input=chunk
            )
            embeddings.append(response.data[0].embedding)

        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]

        # Create FAISS index
        faiss_index = faiss.IndexFlatL2(dimension)
        faiss_index.add(embeddings_array)

        print(f"Created FAISS index with {faiss_index.ntotal} vectors")
        return faiss_index
    
    def search_embeddings(self, query, top_k=3):
        """Search using semantic embeddings"""
        # Embed the query
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = np.array([response.data[0].embedding]).astype('float32')
        
        # Search FAISS index
        distances, indices = self.faiss_index.search(query_embedding, top_k)
        
        # Get top chunks
        results = [self.doc_chunks[idx] for idx in indices[0]]
        
        context = "Relevant chunks from knowledge base (Embeddings):\n\n"
        for i, chunk in enumerate(results, 1):
            context += f"{i}. {chunk[:200]}...\n\n"
        
        return context

    def _build_bm25_index(self):
        """Build BM25 index"""
        chunks = self.doc_chunks

        # Tokenize chunks (simple split on whitespace)
        tokenized_chunks = [chunk.lower().split() for chunk in chunks]

        # Build BM25 index
        bm25_index = BM25Okapi(tokenized_chunks)
        print(f"Created BM25 index with {len(tokenized_chunks)} chunks")
        return bm25_index
    
    def search_bm25(self, query, top_k=3):
        """Search using BM25 ranking"""
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Get top chunks
        results = [self.doc_chunks[idx] for idx in top_indices]
        
        context = "Relevant chunks from knowledge base (BM25):\n\n"
        for i, chunk in enumerate(results, 1):
            context += f"{i}. {chunk[:200]}...\n\n"
        
        return context

    def hybrid_search(self, query, top_k=3):
        """Combine embeddings (semantic) + BM25 (keyword) for best results"""
        # Get semantic results
        semantic_results = self.search_embeddings(query, top_k=top_k)
        # Get keyword results  
        keyword_results = self.search_bm25(query, top_k=top_k)
        
        # Combine both results (simple merge - can be improved with reciprocal rank fusion)
        combined = f"{semantic_results}\n\n{keyword_results}"
        return combined

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results
    
    def system_prompt(self, qa_context=""):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n## CV:\n{self.cv}\n\n"
        
        if qa_context:
            system_prompt += f"\n{qa_context}\n"
        
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        # Search Q&A database for relevant context
        qa_context = self.search_qa(message)

        # Then RAG search for more relevant context
        rag_context = self.hybrid_search(message, top_k=3)

        # Combine Q&A and RAG context
        combined_context = ""
        if qa_context:
            combined_context += f"## Relevant Q&A:\n{qa_context}\n\n"
        if rag_context:
            combined_context += f"## Relevant Information from Documents:\n{rag_context}\n"

        # Build system prompt with combined context
        prompt = self.system_prompt(combined_context)

        messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    