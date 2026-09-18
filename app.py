"""
Web UI backend for the support-triage project.

Wraps the same tool functions used by the MCP server (server.py) as a
small REST API, and serves the static frontend in static/. This gives
the project a browser-based product UI on top of the exact same backend
logic, without needing an MCP client like Claude Desktop.

Run: python app.py
Then open: http://localhost:8000
"""

from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import server

app = FastAPI(title="Support Triage")


def _fn(tool):
    """Tool functions decorated with @mcp.tool() are wrapped; .fn gives the raw function."""
    return getattr(tool, "fn", tool)


class StatusUpdate(BaseModel):
    status: str


@app.get("/api/health")
def health():
    """Reports whether Ollama is reachable, so the UI can show a live status dot."""
    ollama_up = True
    try:
        base_url = server.OLLAMA_URL.rsplit("/api/", 1)[0]
        requests.get(base_url, timeout=2)
    except requests.exceptions.RequestException:
        ollama_up = False
    return {"ollama": ollama_up, "model": server.OLLAMA_MODEL}


@app.get("/api/tickets")
def api_list_tickets(status: Optional[str] = None, category: Optional[str] = None):
    result = _fn(server.list_tickets)(status=status, category=category)
    if result and isinstance(result[0], dict) and "error" in result[0]:
        raise HTTPException(400, result[0]["error"])
    return result


@app.get("/api/tickets/{ticket_id}")
def api_get_ticket(ticket_id: str):
    result = _fn(server.get_ticket)(ticket_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@app.patch("/api/tickets/{ticket_id}/status")
def api_update_status(ticket_id: str, body: StatusUpdate):
    result = _fn(server.update_ticket_status)(ticket_id, body.status)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/tickets/{ticket_id}/classify")
async def api_classify(ticket_id: str):
    # classify_ticket calls Ollama and can take up to ~1 min on CPU-only
    # machines, so it runs in a thread pool to avoid blocking the event loop.
    result = await run_in_threadpool(_fn(server.classify_ticket), ticket_id)
    if "error" in result:
        raise HTTPException(502, result["error"])
    return result


# Mounted last so the /api/* routes above always take priority over static files.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
