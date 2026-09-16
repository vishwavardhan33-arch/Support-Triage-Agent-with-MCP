"""
Support Triage MCP Server
--------------------------
Exposes support-ticket data (currently a local mock dataset standing in for
a Zendesk/email inbox) as MCP tools so an MCP-compatible client (e.g. Claude
Desktop) can list, inspect, and update tickets.

Tools in this file (core plumbing, no AI yet):
    - list_tickets(status=None, category=None)
    - get_ticket(ticket_id)
    - update_ticket_status(ticket_id, status)

classify_ticket() (LLM-based triage) is added in a later step once this
core is working end-to-end.
"""

import json
from pathlib import Path
from typing import Optional

from mcp.server.mcpserver import MCPServer

DATA_PATH = Path(__file__).parent / "data" / "tickets.json"
VALID_STATUSES = {"open", "in_progress", "closed"}

mcp = MCPServer("Support Triage")


def _load_tickets() -> list[dict]:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _save_tickets(tickets: list[dict]) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(tickets, f, indent=2)


@mcp.tool()
def list_tickets(status: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
    """
    List support tickets, optionally filtered.

    Args:
        status: filter by ticket status - "open", "in_progress", or "closed".
        category: filter by ticket category, e.g. "Disbursement Delay".
    """
    tickets = _load_tickets()

    if status:
        if status not in VALID_STATUSES:
            return [{"error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}"}]
        tickets = [t for t in tickets if t["status"] == status]

    if category:
        tickets = [t for t in tickets if t["category"].lower() == category.lower()]

    return tickets


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """
    Get full details of a single ticket by its ID (e.g. "T-1021").
    """
    tickets = _load_tickets()
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    return {"error": f"Ticket '{ticket_id}' not found"}


@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> dict:
    """
    Update a ticket's status.

    Args:
        ticket_id: the ticket to update, e.g. "T-1021".
        status: new status - "open", "in_progress", or "closed".
    """
    if status not in VALID_STATUSES:
        return {"error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}"}

    tickets = _load_tickets()
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = status
            _save_tickets(tickets)
            return t

    return {"error": f"Ticket '{ticket_id}' not found"}


if __name__ == "__main__":
    mcp.run()
