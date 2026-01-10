import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# In-memory store for interactions
interactions = {}

class AgentInteractionRequest(BaseModel):
    input: str
    background: bool = True
    agent_config: Optional[dict] = None

@app.post("/v1alpha/interactions")
async def create_interaction(request: Request):
    print(f"DEBUG: Received request to create interaction")
    body = await request.json()
    interaction_id = f"int_{len(interactions) + 1}"
    is_slow = "slow" in body.get("input", "").lower()
    
    interactions[interaction_id] = {
        "id": interaction_id,
        "status": "IN_PROGRESS",
        "query": body.get("input"),
        "thoughts": ["Initial thought..."],
        "content": "Finished content.",
        "outputs": [{"text": "Finished content."}]
    }
    
    async def event_generator():
        yield f"data: {json.dumps({'interaction': {'id': interaction_id}})}\n\n"
        await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'thought': 'Thinking...'})}\n\n"
        
        if not is_slow:
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'content': {'parts': [{'text': 'Finished content.'}]}})}\n\n"
            interactions[interaction_id]["status"] = "COMPLETED"
        else:
            # End stream without content, stay IN_PROGRESS for a bit
            await asyncio.sleep(0.5)
            # We'll mark it COMPLETED after a short delay so polling can see it
            async def complete_later():
                await asyncio.sleep(2)
                interactions[interaction_id]["status"] = "COMPLETED"
            asyncio.create_task(complete_later())

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/v1alpha/interactions/{interaction_id}")
async def get_interaction(interaction_id: str):
    print(f"DEBUG: Polling interaction {interaction_id}")
    if interaction_id not in interactions:
        return {"error": "Not found"}, 404
    return interactions[interaction_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
