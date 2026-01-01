# Potential Improvements for Gemini Deep Research CLI

## v1: State & Persistence
- **Local Database**: Use SQLite to store research tasks, including `interaction_id` and the final report. This allows resuming interrupted streams and viewing past research.
- **Session Management**: Support follow-up questions by passing the `previous_interaction_id` to new `create_interaction` calls.

## v2: Advanced Features
- **File Search Integration**: Add support for the `file_search` tool to allow research over local documents.
- **Configurable Models**: Allow users to specify different models or versions via CLI flags or a config file.
- **Prompt Steering**: Expose parameters for system instructions to adjust report format, tone, or depth.

## v3: UX & Integration
- **Interactive Mode**: A REPL-like interface for ongoing research conversations.
- **Export Formats**: Support exporting reports to PDF, HTML, or JSON.
- **Agent Hand-off**: Standardized JSON output for easier consumption by other automated agents (like me!).
- **Progress Visualization**: Better UI for the "thinking" steps, perhaps showing the search queries the agent is performing.

## Developer Experience
- **Type Safety**: Use Pydantic models for interaction responses.
- **Unit Testing**: Mock the Interactions API for testing the CLI logic.
- **Better Error Handling**: Explicitly handle 401 (Auth), 429 (Rate Limit), and 404 (Model availability) errors.
