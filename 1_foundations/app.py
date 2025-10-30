from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import sqlite3
import re


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
        reader = PdfReader("me/cameronbell2.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        cv_reader = PdfReader("me/cameronbell_cv.pdf")
        self.cv = ""
        for page in cv_reader.pages:
            text = page.extract_text()
            if text:
                self.cv += text
        with open("me/summary2.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        # Initialize SQLite database
        self.conn = sqlite3.connect('qa_database.db')
        self.cursor = self.conn.cursor()
        self._init_database()
    
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


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
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
        
        # Build system prompt with Q&A context
        prompt = self.system_prompt(qa_context)
        
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
    