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

`pharos-docs` connects to the official Pharos GitBook agentic documentation protocol (`https://docs.pharos.xyz/index.md?ask=<ask>&goal=<goal>`) to deliver concise, synthesized answers with clickable source documentation citations and suggested follow-ups.

- **Natural Language Querying**: Directly accepts plain developer questions (`pharos-docs "How do I deploy a contract?"`).
- **Sourced Citations**: Parses and resolves all documentation sections to absolute URLs.
- **Honest "No Good Answer Found" Detection**: Rejects hallucinations. When an off-topic question or undocumented topic is asked, the tool clearly flags the absence of documentation.
- **Zero Dependencies & Zero Cost**: 100% Python standard library (`urllib`, `json`, `argparse`, `re`). Zero API keys, zero gas, zero subscription costs.
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
                   [--json] [--no-color] [--max-sources MAX_SOURCES] [--version]
                   [query]

Options:
  query                 Natural language question to query Pharos documentation.
  --goal GOAL           Developer goal context (default: 'develop and verify autonomous AI agents on Pharos').
  --endpoint ENDPOINT   Documentation endpoint (default: 'https://docs.pharos.xyz/index.md').
  --timeout TIMEOUT     Timeout in seconds (default: 35).
  --json                Output structured machine-readable JSON.
  --no-color            Disable ANSI color formatting.
  --max-sources N       Maximum number of sources to display (default: 5).
  --version             Show version and exit.
```

## 4. Verification & Testing

Run the automated test suite locally:
```bash
python -m unittest discover -s tests -v
```
