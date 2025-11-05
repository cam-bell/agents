from agents import Runner, trace, gen_trace_id
from clarify_agent import clarify_agent, ClarifyingQuestion
from manager_agent import manager_agent
from writer_agent import ReportData
from email_agent import email_agent


class ResearchManager:

    async def run(
        self,
        query: str,
        clarifying_answers: list[tuple[str, str]] | None = None
    ):
        """Run the deep research process, yielding status and report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/"
                  f"trace?trace_id={trace_id}")
            yield (f"View trace: https://platform.openai.com/traces/"
                   f"trace?trace_id={trace_id}")

            # Enrich query if answers provided
            enriched_query = query
            if clarifying_answers:
                enriched_query = self.enrich_query(query, clarifying_answers)

            # Delegate research to manager agent
            print("Starting autonomous research with manager agent...")
            yield "Starting autonomous research..."

            result = await Runner.run(
                manager_agent,
                f"Research Query: {enriched_query}"
            )

            # Extract report data
            report = result.final_output_as(ReportData)

            yield "Report written, sending email..."

            # Send email separately
            await Runner.run(
                email_agent,
                report.markdown_report
            )

            yield "Email sent, research complete"

            # Display the markdown report in UI
            yield report.markdown_report

    async def generate_clarifying_question(
        self,
        query: str,
        qa_history: list[tuple[str, str]]
    ) -> ClarifyingQuestion:
        """Generate a clarifying question based on query and Q&A history"""
        print("Generating clarifying question...")

        # Build context with previous Q&A
        context = f"Original research query: {query}\n\n"
        if qa_history:
            context += "Previous clarifying questions and answers:\n"
            for i, (q, a) in enumerate(qa_history, 1):
                context += f"{i}. Q: {q}\n   A: {a}\n\n"
        context += ("Generate the next clarifying question to better "
                    "understand the user's needs.")

        result = await Runner.run(clarify_agent, context)
        return result.final_output_as(ClarifyingQuestion)

    def enrich_query(
        self,
        original_query: str,
        qa_pairs: list[tuple[str, str]]
    ) -> str:
        """Combine original query with Q&A pairs into enriched context"""
        if not qa_pairs or all(not answer.strip() for _, answer in qa_pairs):
            return original_query

        enriched = f"Original Query: {original_query}\n\nAdditional Context:\n"
        for question, answer in qa_pairs:
            if answer.strip():
                enriched += f"- {question}\n  Answer: {answer}\n"
        return enriched
