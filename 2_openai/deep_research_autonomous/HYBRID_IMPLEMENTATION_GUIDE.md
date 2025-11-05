# Hybrid Approach Implementation Guide

## Overview

This implementation follows the **hybrid approach**: combining Python-controlled clarifying questions with agent-based research orchestration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Gradio)                  │
│              deep_research_interactive.py                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              ResearchManager (Python Class)                  │
│                  research_manager.py                         │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │  PYTHON-CONTROLLED (Sequential)                │        │
│  │  • generate_clarifying_question()              │        │
│  │  • enrich_query()                              │        │
│  │  Reason: Precise UI control needed             │        │
│  └────────────────────────────────────────────────┘        │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │  AGENT-CONTROLLED (Autonomous)                 │        │
│  │  • Delegates to manager_agent                  │        │
│  │  Reason: Flexible, self-organizing research    │        │
│  └────────────────────────────────────────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Manager Agent (Orchestrator)                    │
│                  manager_agent.py                            │
│                                                              │
│  Tools:                                                      │
│  ├─ planner_tool  (from planner_agent)                     │
│  ├─ search_tool   (from search_agent)                      │
│  └─ writer_tool   (from writer_agent)                      │
│                                                              │
│  Handoff:                                                    │
│  └─ email_agent                                             │
└─────────────────────────────────────────────────────────────┘
```

## What Changed

### 1. NEW FILE: `manager_agent.py`

**Purpose:** Autonomous orchestrator for the research workflow

**Key components:**

- Converts individual agents (planner, search, writer) to tools
- Creates manager agent with clear workflow instructions
- Uses handoff pattern for email agent

**Why this way:**

- Manager agent can decide tool execution order
- Natural parallelization of searches
- Better error handling through LLM reasoning
- Follows OpenAI Agents SDK best practices

```python
# Key pattern:
planner_tool = planner_agent.as_tool(...)
search_tool = search_agent.as_tool(...)
writer_tool = writer_agent.as_tool(...)

manager_agent = Agent(
    tools=[planner_tool, search_tool, writer_tool],
    handoffs=[email_agent],
    ...
)
```

### 2. MODIFIED: `research_manager.py`

**Before:** 122 lines - orchestrated everything in Python
**After:** 67 lines - focused on clarifying questions only

**What stayed:**

- `generate_clarifying_question()` - Perfect for sequential UI
- `enrich_query()` - Combines Q&A with original query
- These methods give us precise control over the UI flow

**What changed:**

- `run()` method now delegates to manager_agent
- Removed: `plan_searches()`, `perform_searches()`, `search()`,
  `write_report()`, `send_email()`
- These are now handled autonomously by manager_agent

**Why this way:**

- Clarifying questions need precise UI control (one at a time)
- Research workflow benefits from agent autonomy
- Much simpler, cleaner code

### 3. UNCHANGED: Everything else

- `deep_research_interactive.py` - UI works perfectly as-is
- `clarify_agent.py` - Sequential question generation
- `planner_agent.py` - Search planning
- `search_agent.py` - Web search
- `writer_agent.py` - Report writing
- `email_agent.py` - Email formatting and sending

## How It Works

### Step-by-Step Flow

```
1. User enters query in UI
   └─> deep_research_interactive.py

2. UI asks clarifying questions (3 times)
   └─> ResearchManager.generate_clarifying_question()
   └─> User answers each question
   └─> Context accumulates

3. After 3 Q&A pairs, UI starts research
   └─> ResearchManager.enrich_query(query, qa_pairs)
   └─> ResearchManager.run(enriched_query)

4. ResearchManager delegates to manager agent
   └─> Runner.run(manager_agent, enriched_query)

5. Manager agent orchestrates research autonomously:
   a. Calls planner_tool → gets search plan
   b. Calls search_tool for each search term
      - Can parallelize if efficient
   c. Calls writer_tool with query + all search results
   d. Hands off to email_agent
      - Formats as HTML
      - Sends email

6. Result flows back to UI
   └─> User sees final report
```

### Example Execution Trace

```
USER: "Commercial applications of Agentic AI?"

Q1: "Are you looking for current or emerging applications?"
A1: "Emerging in 2025"

Q2: "Which industries?"
A2: "Healthcare and finance"

Q3: "What aspects matter most?"
A3: "Business impact and ROI"

ENRICHED QUERY:
"Commercial applications of Agentic AI?
Context:
- Timeframe: Emerging in 2025
- Industries: Healthcare and finance
- Focus: Business impact and ROI"

MANAGER AGENT (autonomous):
→ planner_tool: Generate 5 search terms
  ✓ "Agentic AI healthcare 2025 ROI"
  ✓ "Autonomous agents financial services business impact"
  ✓ ...

→ search_tool x5: Execute all searches (parallel)
  ✓ Search 1 complete → summary
  ✓ Search 2 complete → summary
  ...

→ writer_tool: Create comprehensive report
  ✓ 1000+ word report with citations

→ handoff email_agent: Format and send
  ✓ Email sent

RESULT: Final report displayed in UI
```

## Benefits of Hybrid Approach

| Aspect                   | Python Control | Agent Control    |
| ------------------------ | -------------- | ---------------- |
| **Clarifying Questions** | ✅ Perfect     | ❌ Unpredictable |
| **Research Workflow**    | ❌ Rigid       | ✅ Flexible      |
| **UI Integration**       | ✅ Precise     | ❌ Hard to sync  |
| **Parallelization**      | ❌ Manual      | ✅ Natural       |
| **Error Recovery**       | ❌ Try/catch   | ✅ LLM reasoning |
| **Code Simplicity**      | ❌ Complex     | ✅ Simple        |

### Why hybrid wins:

1. **Control where needed:** Sequential Q&A requires precise ordering
2. **Autonomy where valuable:** Research benefits from flexible execution
3. **Best of both worlds:** Simple code + powerful execution

## Key Improvements

### Code Reduction

- **Before:** 122 lines in research_manager.py
- **After:** 67 lines in research_manager.py
- **New:** 54 lines in manager_agent.py
- **Net:** Cleaner, more maintainable

### Autonomy

- Manager agent can decide optimal tool execution
- Natural parallelization of searches
- Better error handling through reasoning

### Maintainability

- Clear separation of concerns
- Individual agents remain simple and focused
- Easy to add new tools or modify workflow

## Usage

### Run the interactive version:

```bash
cd /Users/cameronbell/Projects/agents/2_openai/deep_research_autonomous
python deep_research_interactive.py
```

### Run the basic version (no clarifying questions):

```bash
python deep_research.py
```

## Cost Impact

### Additional LLM calls (vs old approach):

- Manager agent reasoning: +1-2 calls
- Tool selection decisions: +1-2 calls
- **Total additional cost:** ~$0.002-0.004 per research

### Value gained:

- More flexible execution
- Better error recovery
- Natural parallelization
- Cleaner, simpler code

## Monitoring

View execution traces:

```
View trace: https://platform.openai.com/traces/trace?trace_id=<id>
```

Each run provides a trace ID to see:

- Manager agent decisions
- Tool calls and results
- Handoff execution
- Full execution flow

## Future Enhancements

### Possible improvements:

1. **Dynamic question count:** Let agent decide 1-5 questions
2. **Quality evaluation:** Add eval agent to validate reports
3. **Multi-round research:** Agent can request follow-up searches
4. **Adaptive planning:** Adjust searches based on initial results
5. **User feedback loop:** Allow user to request refinements

## Troubleshooting

### Manager agent not calling all tools?

- Check INSTRUCTIONS clarity
- Review trace to see reasoning
- May need to strengthen "MUST use ALL tools" directive

### Searches not executing in parallel?

- Manager agent decides this automatically
- Check trace to see execution order
- LLM may choose sequential for good reasons

### Email not sending?

- Check SENDGRID_API_KEY in .env
- Verify handoff is executing (check trace)
- Ensure email addresses are verified senders

## Technical Notes

### Why agents-as-tools?

- Agent gets full context and output from each tool
- LLM can reason about results
- Natural error handling
- Better than simple function calls

### Why handoff for email?

- Represents workflow transition
- Email agent is complex (subject, HTML, send)
- Natural delegation pattern

### Why keep clarifying questions in Python?

- UI needs precise control
- One question at a time, in order
- User experience is critical here
- No benefit from agent autonomy

## Comparison to Original

### Original (Python orchestration):

```python
search_plan = await self.plan_searches(query)
search_results = await self.perform_searches(search_plan)
report = await self.write_report(query, search_results)
await self.send_email(report)
```

### New (Agent orchestration):

```python
result = await Runner.run(
    manager_agent,
    f"Research Query: {enriched_query}"
)
```

**Result:**

- 55 lines of orchestration code → 5 lines
- But gained autonomy, flexibility, and better error handling
