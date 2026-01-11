# Research CLI Reference

## Database Schema
The CLI stores data in a SQLite database located at `~/.research-cli/history.db`.

### `research_tasks` Table
- `id`: Autoincrementing primary key.
- `interaction_id`: The ID returned by the Gemini API.
- `query`: The original research query.
- `model`: The model used for research.
- `status`: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, or `ERROR`.
- `report`: The final Markdown output.
- `created_at`: Timestamp of creation.

## API Integration
The tool uses the `google-genai` Python SDK.
- **Base URL**: Can be overridden with `GEMINI_API_BASE_URL`.
- **API Version**: Hardcoded to `v1alpha`.
- **Interactions API**: Uses `client.interactions.create` with `background=True` and `stream=True`.

## Troubleshooting
- **Missing API Key**: Set `GEMINI_API_KEY`.
- **No Content**: Check if the task is still `IN_PROGRESS` using `list` and `show`.
- **Slow Performance**: Deep research naturally takes 1-5 minutes depending on query complexity.
