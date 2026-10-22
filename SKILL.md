---
name: pharos-doc-search-cli
description: Official command-line search tool on top of Pharos Developer Docs MCP interface.
version: 1.0.0
author: JimmyOgb
license: MIT
metadata:
  track: Developer Docs MCP
  task: doc-search-cli
  points: 50
  cost: $0.00
  dependencies: none (Python standard library only)
---

# Pharos Doc-Search CLI (`pharos-docs`)

A lightweight, zero-dependency command-line interface for querying official Pharos Developer Documentation directly from the terminal. Built for developers and autonomous AI agents during the **Pharos Season of AI — Agent Arena**.

## 1. Overview & Capabilities

`pharos-docs` wraps the official Pharos Developer Docs Model Context Protocol (MCP) server (`https://docs.pharos.xyz/~gitbook/mcp`) via Streamable HTTP / Server-Sent Events (SSE) JSON-RPC 2.0 to deliver concise, synthesized answers with clickable source documentation citations, keyword search, page retrieval, and suggested follow-ups.

- **Developer Docs MCP Wrapper**: Direct client for official MCP tools (`askQuestion`, `searchDocumentation`, `getPage`, `sendFeedback`).
- **Natural Language Querying**: Directly accepts plain developer questions (`pharos-docs "How do I deploy a contract?"`).
- **Keyword Search & Page Fetching**: Dedicated flags (`--search <term>` and `--page <path/url>`).
- **Sourced Citations**: Parses and resolves all documentation sections to absolute URLs.
- **Honest "No Good Answer Found" Detection**: Rejects hallucinations. When an off-topic question or undocumented topic is asked, the tool clearly flags the absence of documentation and exits with code `2`.
- **Zero Dependencies & Zero Cost**: 100% Python standard library (`urllib`, `json`, `argparse`, `re`). Zero external packages, zero API keys, zero gas, zero subscription costs.
- **Dual Output Modes**: Formatted terminal output for human developers; structured `--json` mode for agentic workflows.

## 2. Installation & Quickstart

### Direct Invocation (No installation required)
```bash
python -m pharos_docs.cli "What is the Atlantic testnet RPC URL and chain ID?"
```

### Global / Local Installation
```bash
pip install -e .
pharos-docs "How do I deploy a contract?"
```

## 3. Command Reference

```text
usage: pharos-docs [-h] [--goal GOAL] [--endpoint ENDPOINT] [--timeout TIMEOUT]
                   [--search SEARCH] [--page PAGE] [--list-tools]
                   [--json] [--no-color] [--max-sources MAX_SOURCES] [--version]
                   [query]

Options:
  query                 Natural language question to query Pharos documentation.
  --goal GOAL           Developer goal context (default: 'develop and verify autonomous AI agents on Pharos').
  --endpoint ENDPOINT   Documentation MCP endpoint (default: 'https://docs.pharos.xyz/~gitbook/mcp').
  --timeout TIMEOUT     Timeout in seconds (default: 35).
  --search SEARCH       Search documentation using the Docs MCP searchDocumentation tool.
  --page PAGE           Fetch a specific doc page using Docs MCP getPage tool.
  --list-tools          Discover and list tools exposed by the Docs MCP server.
  --json                Output structured machine-readable JSON.
  --no-color            Disable ANSI color formatting.
  --max-sources N       Maximum number of sources to display (default: 5).
  --version             Show version and exit.
```

## 4. Verification & Testing

Run the automated test suite locally:
```bash
# Run unit tests with offline mock protocol fixtures:
python -m unittest discover -s tests -v

# Run live integration verification against https://docs.pharos.xyz/~gitbook/mcp:
RUN_LIVE_TESTS=1 python -m unittest discover -s tests -v
```
