from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
from clarify_agent import clarify_agent, ClarifyingQuestion

class ResearchManager:

    async def run(self, query: str, clarifying_answers: list[str] | None = None):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # Enrich query if answers provided
            enriched_query = query
            if clarifying_answers:
                # Use provided Q&A pairs to enrich query
                enriched_query = self.enrich_query(query, clarifying_answers)
            
            print("Starting research...")
            search_plan = await self.plan_searches(enriched_query)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(enriched_query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def generate_clarifying_question(self, query: str, qa_history: list[tuple[str, str]]) -> ClarifyingQuestion:
        """Generate a single clarifying question based on query and previous Q&A history"""
        print("Generating clarifying question...")
        
        # Build context with previous Q&A
        context = f"Original research query: {query}\n\n"
        if qa_history:
            context += "Previous clarifying questions and answers:\n"
            for i, (q, a) in enumerate(qa_history, 1):
                context += f"{i}. Q: {q}\n   A: {a}\n\n"
        context += "Generate the next clarifying question to better understand the user's needs."
        
        result = await Runner.run(
            clarify_agent,
            context,
        )
        return result.final_output_as(ClarifyingQuestion)

    def enrich_query(self, original_query: str, qa_pairs: list[tuple[str, str]]) -> str:
        """Combine original query with Q&A pairs into enriched context"""
        if not qa_pairs or all(not answer.strip() for _, answer in qa_pairs):
            return original_query
    
        enriched = f"Original Query: {original_query}\n\nAdditional Context:\n"
        for question, answer in qa_pairs:
            if answer.strip():
                enriched += f"- {question}\n  Answer: {answer}\n"
        return enriched


    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
