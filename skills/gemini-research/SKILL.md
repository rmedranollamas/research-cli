---
name: gemini-research
description: Perform deep, multi-step research on complex queries using the Gemini Deep Research agent.
metadata:
  version: 0.1.0
  author: Ramón
---

# Gemini Research Skill

This skill enables the agent to utilize the `research` CLI tool for performing in-depth research. It interfaces with the Gemini Deep Research agent, which can perform multi-step analysis, web searching, and thought processing.

## When to Use
- When a user asks a complex question that cannot be answered with a simple search.
- When detailed reports or synthesis of multiple sources is required.
- When you need to see the "reasoning" process of the research agent.

## Core Commands

### Start Research
To initiate a new research task, use the `run` subcommand.
```bash
research run "QUERY"
```
*Tip: Provide a specific, detailed query for better results.*

### List Recent Tasks
To see a history of research tasks and their unique IDs:
```bash
research list
```

### Show Task Details
To retrieve the report of a specific task by its ID:
```bash
research show <ID>
```

### Exporting Reports
To save a research report directly to a file:
```bash
research run "QUERY" --output filename.md
# OR for an existing task
research show <ID> --output filename.md

## Advanced Configuration
- **Model Selection**: Use `--model <MODEL_ID>` to override the default.
- **Environment**: Ensure `GEMINI_API_KEY` is set in the environment.

## Best Practices
1. **Iterative Research**: If the initial report is too broad, use the information gathered to run a more targeted research task.
2. **Task Tracking**: Always use `list` if you lose track of an ongoing task.
3. **Patience**: Deep research takes time. The tool provides a progress spinner and streams "thoughts" to indicate activity.
