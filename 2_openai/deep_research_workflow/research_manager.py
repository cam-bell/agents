from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from evaluator_agent import evaluator_agent, ReportEvaluation
from router_agent import router_agent, QueryRoute
import asyncio
from clarify_agent import clarify_agent, ClarifyingQuestion

MAX_REVISION_ATTEMPTS = 2

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
            
            # ROUTING: Determine research approach
            yield "Analyzing query type..."
            route = await self.route_query(enriched_query)
            yield f"Route: {route.route} ({route.reasoning})"
            
            print("Starting research...")
            search_plan = await self.plan_searches(enriched_query, route.num_searches)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            
            # EVALUATOR-OPTIMIZER: Write report with quality feedback loop
            report = await self.write_report_with_evaluation(enriched_query, search_results, route)
            
            yield "Report finalized, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report
        

    async def route_query(self, query: str) -> QueryRoute:
        """Determine the best research route for the query"""
        print("Routing query...")
        result = await Runner.run(
            router_agent,
            f"Query: {query}",
        )
        route = result.final_output_as(QueryRoute)
        print(f"Route selected: {route.route} - {route.reasoning}")
        return route

    async def plan_searches(self, query: str, num_searches: int = 5) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print(f"Planning {num_searches} searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}\nNumber of searches to plan: {num_searches}",
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

    async def write_report(self, query: str, search_results: list[str], feedback: str = "") -> ReportData:
        """ Write the report for the query """
        print("Writing report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        if feedback:
            input += f"\n\nPrevious attempt feedback:\n{feedback}\n\nPlease address these issues in your revised report."
        
        result = await Runner.run(
            writer_agent,
            input,
        )
        return result.final_output_as(ReportData)

    async def evaluate_report(self, query: str, report: ReportData, search_results: list[str]) -> ReportEvaluation:
        """Evaluate report quality"""
        print("Evaluating report quality...")
        input = (
            f"Query: {query}\n\n"
            f"Report:\n{report.markdown_report}\n\n"
            f"Search results used:\n{search_results[:3]}"  # Sample of results
        )
        result = await Runner.run(
            evaluator_agent,
            input,
        )
        evaluation = result.final_output_as(ReportEvaluation)
        print(f"Evaluation: {'✓ Acceptable' if evaluation.is_acceptable else '✗ Needs revision'} (Score: {evaluation.score}/10)")
        return evaluation

    async def write_report_with_evaluation(self, query: str, search_results: list[str], route: QueryRoute) -> ReportData:
        """Write report with quality evaluation and revision loop"""
        attempt = 0
        feedback = ""
        
        while attempt < MAX_REVISION_ATTEMPTS:
            attempt += 1
            
            # Write report
            report = await self.write_report(query, search_results, feedback)
            
            # Evaluate (skip evaluation for quick queries to save cost)
            if route.route == "quick" or attempt >= MAX_REVISION_ATTEMPTS:
                print(f"Report complete (attempt {attempt})")
                return report
            
            evaluation = await self.evaluate_report(query, report, search_results)
            
            if evaluation.is_acceptable:
                print(f"✓ Report approved on attempt {attempt}")
                return report
            
            # Prepare feedback for revision
            feedback = f"Issues: {', '.join(evaluation.issues)}\nSuggestions: {evaluation.suggestions}"
            print(f"Revision needed (attempt {attempt}/{MAX_REVISION_ATTEMPTS})")
        
        print("Max revisions reached, returning final report")
        return report
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
