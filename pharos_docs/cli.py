"""
Pharos Doc-Search CLI Entry Point
Provides a terminal command-line interface for querying Pharos Developer Docs via Developer Docs MCP.

Usage:
    pharos-docs "How do I deploy a contract?"
    python -m pharos_docs.cli "What is the Atlantic testnet chain ID?"
    pharos-docs --json "How to use Pharos MCP?"
    pharos-docs --search "Atlantic RPC"
    pharos-docs --list-tools
"""

import sys
import json
import argparse
from typing import Optional, List
from .client import (
    PharosDocsMCPClient,
    PharosDocsClient,
    DEFAULT_DOCS_MCP_ENDPOINT,
    DEFAULT_DOCS_ENDPOINT,
    DEFAULT_GOAL,
    DEFAULT_TIMEOUT,
)

# Configure UTF-8 encoding on Windows consoles where possible to prevent charmap errors on Unicode docs
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# ANSI terminal colors (gracefully ignored if not supported or disabled)
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_terminal_output(result: dict, no_color: bool = False, max_sources: int = 5) -> str:
    """Formats structured query result for readable terminal output."""
    c_cyan = "" if no_color else CYAN
    c_green = "" if no_color else GREEN
    c_yellow = "" if no_color else YELLOW
    c_bold = "" if no_color else BOLD
    c_dim = "" if no_color else DIM
    c_reset = "" if no_color else RESET

    lines = []
    lines.append(f"{c_bold}{c_cyan}=== Pharos Developer Docs Search ==={c_reset}")
    lines.append(f"{c_dim}Query: \"{result['query']}\"{c_reset}")
    lines.append(f"{c_dim}Latency: {result['elapsed_seconds']}s | HTTP: {result['http_status']}{c_reset}")
    lines.append("")

    if not result.get("has_answer", True):
        lines.append(f"{c_bold}{c_yellow}[Notice: No Good Answer Found in Official Docs]{c_reset}")
        lines.append(f"{c_dim}The documentation returned no confident or relevant answer for this specific query:{c_reset}")
        lines.append("")
        if result.get("answer"):
            lines.append(result["answer"])
            lines.append("")
    else:
        lines.append(f"{c_bold}{c_green}[Answer]{c_reset}")
        lines.append(result.get("answer", ""))
        lines.append("")

    sources: List[dict] = result.get("sources", [])
    if sources:
        lines.append(f"{c_bold}[Sources & Documentation References]{c_reset}")
        display_sources = sources[:max_sources]
        for idx, src in enumerate(display_sources, 1):
            lines.append(f"  {idx}. {src.get('title', 'Doc Section')}")
            lines.append(f"     {c_dim}-> {src.get('url', '')}{c_reset}")
        if len(sources) > max_sources:
            lines.append(f"  {c_dim}... and {len(sources) - max_sources} more reference sections.{c_reset}")
        lines.append("")

    follow_ups: List[dict] = result.get("follow_ups", [])
    if follow_ups:
        lines.append(f"{c_bold}[Suggested Follow-Up Queries]{c_reset}")
        for q in follow_ups[:3]:
            lines.append(f"  * {q.get('question', '')}")
        lines.append("")

    return "\n".join(lines).strip()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint."""
    parser = argparse.ArgumentParser(
        prog="pharos-docs",
        description="Query Pharos Developer Docs via official Developer Docs MCP server."
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default=None,
        help="Natural language question to query Pharos documentation with."
    )
    parser.add_argument(
        "--goal",
        type=str,
        default=DEFAULT_GOAL,
        help=f"High-level developer goal context (default: '{DEFAULT_GOAL}')."
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=DEFAULT_DOCS_MCP_ENDPOINT,
        help=f"Base documentation MCP endpoint (default: '{DEFAULT_DOCS_MCP_ENDPOINT}')."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of rendered terminal text."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI terminal color output."
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=5,
        help="Maximum number of source references to display (default: 5)."
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Explicitly query using the searchDocumentation MCP tool."
    )
    parser.add_argument(
        "--page",
        type=str,
        default=None,
        help="Fetch full markdown page content using the getPage MCP tool."
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Discover and display available tools on the Developer Docs MCP server."
    )
    parser.add_argument(
        "--version",
        action="version",
        version="pharos-docs 2.0.0",
        help="Show version and exit."
    )

    args = parser.parse_args(argv)

    client = PharosDocsMCPClient(
        endpoint=args.endpoint,
        timeout=args.timeout
    )

    # 1. Discover tools command
    if args.list_tools:
        try:
            client.initialize()
            tools = client.list_tools()
            if args.json:
                print(json.dumps({
                    "serverInfo": client.server_info,
                    "tools": tools
                }, indent=2))
            else:
                s_name = client.server_info.get("name", "Docs MCP") if client.server_info else "Docs MCP"
                print(f"=== Pharos Developer Docs MCP Tools ({s_name}) ===")
                for t in tools:
                    print(f"- {t['name']}: {t.get('description', '').strip()[:100]}...")
            return 0
        except Exception as e:
            print(f"[Doc-Search Error] {e}", file=sys.stderr)
            return 1

    # 2. Get full page content
    if args.page:
        try:
            res = client.get_page(args.page)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"=== Pharos Docs Page ({res['elapsed_seconds']}s) ===")
                print(res["answer"])
            return 0
        except Exception as e:
            print(f"[Doc-Search Error] {e}", file=sys.stderr)
            return 1

    # 3. Explicit search mode
    if args.search:
        try:
            res = client.search_documentation(args.search)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"=== Pharos Docs Search Results: '{args.search}' ({res['elapsed_seconds']}s) ===")
                print(res["answer"])
            return 0
        except Exception as e:
            print(f"[Doc-Search Error] {e}", file=sys.stderr)
            return 1

    # 4. Standard question query (positional or stdin)
    query_text = args.query
    if query_text == "-":
        query_text = sys.stdin.read().strip()

    if not query_text:
        parser.print_help(sys.stderr)
        return 1

    result = client.query(query_text, args.goal)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result["success"]:
            print(f"[Doc-Search Error] {result.get('error', 'Unknown failure')}", file=sys.stderr)
            return 1
        print(format_terminal_output(result, no_color=args.no_color, max_sources=args.max_sources))

    if not result["success"]:
        return 1
    if not result.get("has_answer", True):
        # Exit code 2 signifies "no answer found", distinguishing from fatal errors
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
