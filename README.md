# Support Triage MCP

An MCP (Model Context Protocol) server that exposes a support-ticket inbox as
tools an AI client can use to list, inspect, triage, and update tickets.
The dataset here is mocked (styled after a home-loan partner-support inbox:
loan status queries, document issues, disbursement delays, KYC, etc.) but the
server is written so a real ticket source (Zendesk, email, a helpdesk API)
could be swapped in later without changing the tool interface.

## Status

Core plumbing is working: `list_tickets`, `get_ticket`, and
`update_ticket_status`. AI-based triage (`classify_ticket`) is the next
milestone — see [Roadmap](#roadmap).

## Project structure

```
support-triage-mcp/
├── server.py              # MCP server + tool definitions
├── data/
│   ├── tickets.json       # mock ticket dataset
│   └── generate_data.py   # regenerates tickets.json
├── tests/
│   └── test_server.py     # smoke tests for the tool functions
├── requirements.txt
├── LICENSE
└── README.md
```

## Setup

```bash
git clone <your-repo-url>
cd support-triage-mcp
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Regenerate the mock dataset any time with:

```bash
python data/generate_data.py
```

Run the test suite:

```bash
pip install pytest
pytest tests/ -v
```

## Running the server standalone

```bash
python server.py
```

This starts the MCP server over stdio, waiting for a client to connect.

## Connecting to Claude Desktop

Add this to your Claude Desktop MCP config
(`claude_desktop_config.json` — Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "support-triage": {
      "command": "python",
      "args": ["/absolute/path/to/support-triage-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop, then try prompts like:

- "List all open support tickets"
- "Show me ticket T-1021"
- "Mark T-1021 as in_progress"

## Available tools

| Tool | Description |
|---|---|
| `list_tickets(status?, category?)` | List tickets, optionally filtered by status (`open` / `in_progress` / `closed`) and/or category. |
| `get_ticket(ticket_id)` | Get full details of one ticket by ID. |
| `update_ticket_status(ticket_id, status)` | Update a ticket's status. |

## Roadmap

- [ ] `classify_ticket(ticket_id)` — LLM-based category/priority/sentiment classification + suggested response draft
- [ ] Retrieve similar past tickets as context before classifying (RAG-style)
- [ ] GitHub Actions CI (lint + pytest on every push)
- [ ] Swap the mock dataset for a real ticket source

## Notes on the MCP SDK version

This project uses `mcp` v2.x, where the server class was renamed from
`FastMCP` to `MCPServer` (`mcp.server.mcpserver.MCPServer`). The decorator
API (`@mcp.tool()`) and `mcp.run()` are unchanged from v1. If you're
following older MCP tutorials that import `from mcp.server.fastmcp import
FastMCP`, either update the import as above or pin `mcp<2.0.0`.
