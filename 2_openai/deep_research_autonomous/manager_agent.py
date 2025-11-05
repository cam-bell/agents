from agents import Agent
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent, ReportData

# Convert agents to tools
planner_tool = planner_agent.as_tool(
    tool_name="planner_tool",
    tool_description="Create a comprehensive search plan with multiple search "
    "terms for the research query"
)

search_tool = search_agent.as_tool(
    tool_name="search_tool",
    tool_description="Perform a web search on a specific term and return a "
    "concise summary of results"
)

writer_tool = writer_agent.as_tool(
    tool_name="writer_tool",
    tool_description=(
        "Write a comprehensive research report based on the query "
        "and search results"
    )
)

INSTRUCTIONS = """You are a research manager orchestrating a multi-step \
research workflow.

Your workflow:
1. Plan searches: Use planner_tool with the enriched query to generate a \
search plan
2. Execute searches: Use search_tool for EACH search term in the plan
   - Call search_tool once per search term
   - You can call them in parallel if efficient
3. Write report: Use writer_tool with the enriched query and all search \
results
4. Return the complete report with markdown_report, short_summary, and \
follow_up_questions

IMPORTANT:
- Use ALL tools in order
- Execute search_tool for every search term from the plan
- Collect all search results before writing
- Return the full ReportData from writer_tool as your final output
"""

manager_agent = Agent(
    name="ResearchManagerAgent",
    instructions=INSTRUCTIONS,
    tools=[planner_tool, search_tool, writer_tool],
    model="gpt-4o-mini",
    output_type=ReportData,
)
