# Support Triage MCP

An MCP (Model Context Protocol) server that exposes a support-ticket inbox as
tools an AI client can use to list, inspect, triage, and update tickets.
The dataset here is mocked (styled after a home-loan partner-support inbox:
loan status queries, document issues, disbursement delays, KYC, etc.) but the
server is written so a real ticket source (Zendesk, email, a helpdesk API)
could be swapped in later without changing the tool interface.

## Status

Core plumbing (`list_tickets`, `get_ticket`, `update_ticket_status`) and
LLM-based triage (`classify_ticket`, with RAG-style retrieval of similar
past tickets) are both working. `classify_ticket` runs entirely on a local,
open-source LLM via [Ollama](https://ollama.com) — no API key, no per-call
cost. See [Roadmap](#roadmap) for what's next.

### Setting up Ollama (needed for `classify_ticket`)

1. Install Ollama from [ollama.com](https://ollama.com) (Windows/Mac/Linux).
2. Pull a model (one-time download, then it runs fully offline):
   ```bash
   ollama pull llama3.2
   ```
   `llama3.2` (3B) is small and fast enough for CPU-only laptops. For
   better classification quality if your machine can handle it, try
   `ollama pull llama3.1` (8B) or `ollama pull mistral` — just set
   `OLLAMA_MODEL` to match (see below).
3. Ollama runs a local server automatically after install. If it's not
   running, start it with:
   ```bash
   ollama serve
   ```

By default the server talks to `http://localhost:11434` and uses the
`llama3.2` model. Override either with environment variables if needed:

```bash
# macOS/Linux
export OLLAMA_MODEL="mistral"

# Windows (PowerShell)
$env:OLLAMA_MODEL="mistral"
```

`list_tickets`, `get_ticket`, and `update_ticket_status` don't need Ollama
at all — only `classify_ticket` does.

## Evaluation

`evaluate.py` measures two things against the mock dataset:

1. **Routing accuracy** — how often `classify_ticket`'s predicted `category`
   and `priority` match the dataset's ground-truth labels (baked in by
   `generate_data.py`).
2. **LLM-as-judge** — there's no ground truth for the *quality* of the
   drafted `suggested_response`, so a second local model scores it on
   relevance, professionalism, and actionability (1-5 each).

```bash
# Quick run: 10 tickets, routing accuracy + judge scores
python evaluate.py --limit 10

# Use a different, larger model as judge to reduce self-judging bias
python evaluate.py --limit 10 --judge-model mistral

# Routing accuracy only, no judge step (faster)
python evaluate.py --limit 10 --no-judge
```

Each ticket costs 1-2 local LLM calls, so on a CPU-only laptop start with
`--limit 5-10` before running the full 40-ticket dataset — otherwise it can
take a while (see [Status](#status) for rough per-call timing). Full
per-ticket results are written to `eval_results.json` (git-ignored, since
it's a run artifact, not source).

**Note on self-judging bias:** if the same model both classifies and judges,
it tends to rate its own drafts generously. Passing `--judge-model` with a
different (ideally larger) model gives a more honest signal.

## Project structure

```
support-triage-mcp/
├── server.py              # MCP server + tool definitions
├── evaluate.py            # routing-accuracy + LLM-as-judge evaluation harness
├── retrieval.py           # TF-IDF similar-ticket retrieval (RAG-style)
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
- "Classify ticket T-1021 and draft a first response"

## Available tools

| Tool | Description |
|---|---|
| `list_tickets(status?, category?)` | List tickets, optionally filtered by status (`open` / `in_progress` / `closed`) and/or category. |
| `get_ticket(ticket_id)` | Get full details of one ticket by ID. |
| `update_ticket_status(ticket_id, status)` | Update a ticket's status. |
| `classify_ticket(ticket_id)` | Category/priority/sentiment classification + a suggested first response, using a local open-source LLM (Ollama) and similar past tickets as reference context. |

## Roadmap

- [ ] GitHub Actions CI (lint + pytest on every push — no Ollama needed since tests mock the LLM call)
- [ ] Swap TF-IDF retrieval for real embeddings (a local embedding model, e.g. via `ollama pull nomic-embed-text`)
- [ ] Swap the mock dataset for a real ticket source
- [ ] Try larger local models (`llama3.1`, `mistral`) and compare routing accuracy vs. `llama3.2`

## Notes on the MCP SDK version

This project uses `mcp` v2.x, where the server class was renamed from
`FastMCP` to `MCPServer` (`mcp.server.mcpserver.MCPServer`). The decorator
API (`@mcp.tool()`) and `mcp.run()` are unchanged from v1. If you're
following older MCP tutorials that import `from mcp.server.fastmcp import
FastMCP`, either update the import as above or pin `mcp<2.0.0`.
