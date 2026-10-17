# Pharos Doc-Search CLI (`pharos-docs`)

[![Pharos Agent Arena](https://img.shields.io/badge/Pharos_Agent_Arena-Task_4:_Doc--Search_CLI-blue.svg)](https://pharos-agent-arena.vercel.app/tasks/doc-search-cli)
[![Difficulty: Easy](https://img.shields.io/badge/Difficulty-Easy_(50_pts)-brightgreen.svg)](https://pharos-agent-arena.vercel.app/tasks/doc-search-cli)
[![Cost: $0.00](https://img.shields.io/badge/Cost-$0.00_(Zero_Cost)-success.svg)](https://docs.pharos.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Dependencies: 0](https://img.shields.io/badge/Dependencies-0_(Python_Stdlib_Only)-blueviolet.svg)](pyproject.toml)

> **A fast, zero-dependency command-line interface on top of the Pharos Developer Docs MCP interface.**
> Built by **[JimmyOgb](https://github.com/JimmyOgb)** for the official **Pharos Season of AI — Agent Arena**.

---

## Overview

The **Pharos Doc-Search CLI** (`pharos-docs`) allows developers, terminal users, and autonomous agent loops to search official Pharos documentation from the command line and receive concise, synthesized answers with clickable source documentation links and recommended follow-up questions.

Built strictly against the official GitBook agentic documentation protocol (`https://docs.pharos.xyz/index.md?ask=<ask>&goal=<goal>`), this tool adheres to the **$0-first principles** of the Pharos ecosystem:
- **No external Python packages required** (uses only Python 3.9+ standard library: `urllib`, `json`, `argparse`, `re`).
- **No API keys or paid subscriptions**.
- **No blockchain gas or private keys needed**.
- **Honest error handling**: detects low-confidence or irrelevant answers and refuses to hallucinate facts.

---

## Acceptance Criteria Verification Matrix

| Criterion | Requirement Description | Implementation Status | Evidence / Verification |
| :--- | :--- | :--- | :--- |
| **01** | Accepts a natural-language question as input (`pharos-docs "query"`) | **Verified** | Positional argument in `pharos_docs/cli.py` or stdin pipe |
| **02** | Returns concise answer plus links/references to source doc sections | **Verified** | Parsed markdown answer + resolved `[Sources]` links to `https://docs.pharos.xyz/...` |
| **03** | Handles *"no good answer found"* gracefully without inventing facts | **Verified** | `NO_ANSWER_PATTERNS` regex matching + `[Notice: No Good Answer Found]` banner |
| **04** | README with install/usage instructions and 3 example queries with outputs | **Verified** | Documented below with live verified outputs |

---

## Installation & Setup

### Method 1: Local Pip Editable Install (Recommended)

From the project root directory:

```bash
pip install -e .
```

This installs the console script `pharos-docs` directly onto your system PATH.

### Method 2: Standalone Execution (Zero Installation)

Run directly with Python from anywhere:

```bash
python -m pharos_docs.cli "How do I deploy a contract?"
```

On Windows, you can also execute the included batch wrapper directly:

```cmd
bin\pharos-docs.cmd "What is the Atlantic testnet RPC URL and chain ID?"
```

---

## Usage Guide

```text
pharos-docs [OPTIONS] "YOUR_QUESTION_HERE"
```

### Options:

| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `query` | `string` | *(required)* | Natural language question to query Pharos documentation |
| `--goal` | `string` | `develop and verify autonomous AI agents on Pharos` | High-level developer goal context passed to GitBook |
| `--endpoint` | `string` | `https://docs.pharos.xyz/index.md` | Base documentation endpoint |
| `--timeout` | `integer` | `35` | Network request timeout in seconds |
| `--json` | `flag` | `false` | Output machine-readable JSON object |
| `--no-color` | `flag` | `false` | Disable ANSI terminal color sequences |
| `--max-sources` | `integer` | `5` | Maximum number of source references to print |
| `--version` | `flag` | - | Display version information and exit |

---

## Example Queries & Live Verified Outputs

All three example queries below were executed directly against the live official Pharos Developer Docs endpoint (`https://docs.pharos.xyz/index.md`).

### Example 1: Contract Deployment with Foundry / Hardhat

**Command:**
```bash
pharos-docs "How do I deploy a contract?"
```

**Live Verified Terminal Output:**
```text
=== Pharos Developer Docs Search ===
Query: "How do I deploy a contract?"
Latency: 12.12s | HTTP: 200

[Answer]
You can deploy to Pharos with Foundry or Hardhat. For Foundry:

1. Compile and test your contract:

   forge build
   forge test

2. Create a deployment script that loads PRIVATE_KEY, starts broadcasting, and deploys your contract. Set the key:

   export PRIVATE_KEY=<your-private-key>

3. Deploy using the RPC URL for your target Pharos network:

   forge script script/DeployToken.s.sol --rpc-url <PHAROS_RPC_URL> --broadcast

Your deployer wallet needs enough testnet tokens to cover deployment costs. The Write Your First Token guide includes a complete deployment-script example.

With Hardhat, set the PRIVATE_KEY variable and run:

npx hardhat ignition deploy ./ignition/modules/Token.js --network pharos

See the Write Your First Token guide for network configuration.

[Sources & Documentation References]
  1. Write Your First Uniswap Contract
     -> https://docs.pharos.xyz/developer-guide/foundry/write-your-first-uniswap-contract.md
  2. Write Your First Uniswap Contract
     -> https://docs.pharos.xyz/developer-guide/hardhat/write-your-first-uniswap-contract.md
  3. Validator Node Deployment
     -> https://docs.pharos.xyz/node-and-validator-guide/validator-node-deployment.md
  4. Write Your First Token
     -> https://docs.pharos.xyz/developer-guide/foundry/write-your-first-token.md
  5. Write Your First NFT
     -> https://docs.pharos.xyz/developer-guide/hardhat/write-your-first-nft.md
  ... and 5 more reference sections.

[Suggested Follow-Up Queries]
  * Which network should I target first?
  * How much gas to expect on testnet?
  * Where can I find a sample DeployToken.s.sol?
```

---

### Example 2: Network Parameters & Chain ID

**Command:**
```bash
pharos-docs "What is the Atlantic testnet RPC URL and chain ID?"
```

**Live Verified Terminal Output:**
```text
=== Pharos Developer Docs Search ===
Query: "What is the Atlantic testnet RPC URL and chain ID?"
Latency: 6.62s | HTTP: 200

[Answer]
The Atlantic testnet RPC URL is `https://atlantic.dplabs-internal.com`, and its chain ID is `688689`. See Atlantic Testnet.

[Sources & Documentation References]
  1. Atlantic Testnet
     -> https://docs.pharos.xyz/getting-started/network/atlantic-testnet.md
  2. ZAN RPC
     -> https://docs.pharos.xyz/tooling-and-infrastructure/rpc/zan.md
  3. x402 Atlantic Testnet
     -> https://docs.pharos.xyz/developer-guide/x402/x402-atlantic-testnet.md
  4. Node Management
     -> https://docs.pharos.xyz/node-and-validator-guide/node-management.md
  5. Write Your First Token
     -> https://docs.pharos.xyz/developer-guide/hardhat/write-your-first-token.md
  ... and 5 more reference sections.

[Suggested Follow-Up Queries]
  * Is there a WebSocket endpoint as well?
  * Any access limits for Atlantic RPC?
  * Where can I find latest chain ID updates?
```

---

### Example 3: Honest "No Good Answer Found" Handling

When given an out-of-domain, unanswerable, or missing-documentation question, `pharos-docs` does **not** hallucinate. It detects the negative match and displays an explicit notice banner alongside the official system clarification and the closest available documentation topics:

**Command:**
```bash
pharos-docs "What is the recipe for baking chocolate chip cookies on Pharos?"
```

**Live Verified Terminal Output:**
```text
=== Pharos Developer Docs Search ===
Query: "What is the recipe for baking chocolate chip cookies on Pharos?"
Latency: 12.97s | HTTP: 200

[Notice: No Good Answer Found in Official Docs]
The documentation returned no confident or relevant answer for this specific query:

I cannot find a chocolate chip cookie recipe in the docs. The Pharos Skill Engine covers AI-agent tooling for on-chain operations, not baking.

[Sources & Documentation References]
  1. About Pharos
     -> https://docs.pharos.xyz/introduction/readme.md
  2. Why Pharos
     -> https://docs.pharos.xyz/introduction/why-pharos.md
  3. x402 Atlantic Testnet
     -> https://docs.pharos.xyz/developer-guide/x402/x402-atlantic-testnet.md
  4. x402 Pacific Mainnet
     -> https://docs.pharos.xyz/developer-guide/x402/x402-pacific-mainnet.md
  5. Vision & Mission
     -> https://docs.pharos.xyz/introduction/vision-and-mission.md
  ... and 5 more reference sections.

[Suggested Follow-Up Queries]
  * What is the Pharos Skill Engine for.
  * Where can I find on-chain operation commands?
  * Can I bake cookies with this docs set?
```

*Exit code returned: `2` (signifies no confident answer found, allowing calling shell scripts or CI/CD pipelines to react programmatically).*

---

### Example 4: Machine-Readable JSON Mode (For Agent Loops)

**Command:**
```bash
pharos-docs --json "What is the Atlantic testnet chain ID?"
```

**Sample JSON Output:**
```json
{
  "success": true,
  "query": "What is the Atlantic testnet chain ID?",
  "goal": "develop and verify autonomous AI agents on Pharos",
  "endpoint": "https://docs.pharos.xyz/index.md?ask=What+is+the+Atlantic+testnet+chain+ID%3F&goal=develop+and+verify+autonomous+AI+agents+on+Pharos",
  "http_status": 200,
  "elapsed_seconds": 6.62,
  "answer": "The Atlantic testnet RPC URL is `https://atlantic.dplabs-internal.com`, and its chain ID is `688689`.",
  "has_answer": true,
  "sources": [
    {
      "title": "Atlantic Testnet",
      "url": "https://docs.pharos.xyz/getting-started/network/atlantic-testnet.md"
    }
  ],
  "follow_ups": [
    {
      "question": "Is there a WebSocket endpoint as well?",
      "url": "https://docs.pharos.xyz?ask=Is%20there%20a%20WebSocket%20endpoint%20as%20well%3F"
    }
  ],
  "raw_markdown": "# ...",
  "error": null
}
```

---

## Automated Testing Suite

The repository includes a comprehensive unit and integration test suite covering:
1. URL parameter construction and escaping.
2. Handling of empty queries.
3. Response markdown parsing (concise answer extraction, relative link resolution, source citations, follow-ups).
4. Honest "no good answer found" detection heuristics.
5. HTTP errors (HTTP 404, 500, 503).
6. Network / URLError timeouts and socket resets.
7. Malformed or truncated server payloads.
8. CLI exit codes (`0` for success, `1` for error, `2` for no confident answer).
9. Live integration tests against the live `docs.pharos.xyz` endpoint.

To execute the test suite:

```bash
# Run unit tests (offline, instant mocks):
python -m unittest discover -s tests -v

# Run including live integration tests against docs.pharos.xyz:
RUN_LIVE_TESTS=1 python -m unittest discover -s tests -v
```

---

## Project Structure

```text
pharos-doc-search-cli/
├── pharos_docs/
│   ├── __init__.py           # Package exports & version
│   ├── client.py             # PharosDocsClient (GitBook Agentic API client)
│   └── cli.py                # Command-line entrypoint & terminal formatter
├── bin/
│   ├── pharos-docs           # POSIX executable script
│   └── pharos-docs.cmd       # Windows CMD batch script
├── tests/
│   ├── test_client.py        # 10 client unit tests (mocks, error handling)
│   ├── test_cli.py           # 7 CLI interface tests (flags, JSON, exit codes)
│   └── test_live.py          # 3 live integration tests against docs.pharos.xyz
├── reports/
│   └── PHAROS_TASK4_DOC_SEARCH_CLI.md  # Comprehensive task audit report
├── pyproject.toml            # Modern pip build configuration
├── setup.py                  # Legacy setup script
├── SKILL.md                  # Pharos Skill Engine package specification
└── README.md                 # Complete documentation & usage guide
```

---

## Author & Attribution

- **Author**: Jimmy Ogb ([@JimmyOgb](https://github.com/JimmyOgb))
- **Program**: [Pharos Season of AI — Agent Arena](https://pharos-agent-arena.vercel.app/)
- **Task**: Task 4 (`doc-search-cli`) — Developer Docs MCP
- **Cost**: **$0.00** (Zero Cost Verified)
- **License**: MIT
