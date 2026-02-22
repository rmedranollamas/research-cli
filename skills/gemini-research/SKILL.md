# Gemini Deep Research Skill

Perform deep research on complex topics using the Gemini Interactions API. This skill uses the `research` CLI to manage long-running research tasks, providing real-time reasoning and comprehensive reports.

## Prerequisites

- `RESEARCH_GEMINI_API_KEY`: Required to access the Gemini Interactions API.

## Tools

### `research_run`

Start a new deep research task.

- **`query`**: (Required) The topic or question to research in depth.
- **`model`**: (Optional) The model ID to use for research (default: `deep-research-pro-preview-12-2025`).

**Example:**

```bash
research run "The impact of solid-state batteries on the EV industry"
```

### `research_think`

Start a new thinking task for rapid reasoning.

- **`query`**: (Required) The topic or question to think about.
- **`model`**: (Optional) The model ID to use for thinking (default: `gemini-2.0-flash-thinking-exp`).

**Example:**

```bash
research think "Why is the sky blue?"
```

### `research_list`

List recent research tasks and their status.

**Example:**

```bash
research list
```

### `research_show`

Show the details and report of a specific research task.

- **`id`**: (Required) The ID of the research task to display.

**Example:**

```bash
research show 5
```
