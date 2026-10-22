"""
Pharos Developer Docs MCP Client
Implements a Model Context Protocol (MCP) client wrapping the official Pharos Developer Docs MCP server.

Official Endpoint:
    POST https://docs.pharos.xyz/~gitbook/mcp

MCP Server Specification:
    Protocol Version: 2024-11-05
    Transport: Streamable HTTP / Server-Sent Events (SSE) JSON-RPC 2.0
    Server Name: docs.pharos.xyz/~gitbook/mcp
    Exposed Tools:
        1. searchDocumentation(query: str)
        2. getPage(url: str)
        3. askQuestion(question: str, goal?: str)
        4. sendFeedback(content: str, pageUrl: str, goal?: str)

Features:
    - 100% Python Standard Library (urllib, re, json, time).
    - Zero external dependencies ($0.00).
    - Session initialization & tools/list discovery.
    - Sourced documentation reference extraction.
    - Honest "No Good Answer Found" detection.
    - No fallback to legacy GitBook HTTP 'ask' endpoint.
"""

import re
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_DOCS_MCP_ENDPOINT = "https://docs.pharos.xyz/~gitbook/mcp"
DEFAULT_DOCS_ENDPOINT = DEFAULT_DOCS_MCP_ENDPOINT  # Backward compatibility
DOCS_BASE_URL = "https://docs.pharos.xyz"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PharosDocSearchCLI/2.0 (+https://github.com/JimmyOgb/pharos-doc-search-cli)"
DEFAULT_GOAL = "develop and verify autonomous AI agents on Pharos"
DEFAULT_TIMEOUT = 35

# Known patterns where the documentation model acknowledges no relevant answer
NO_ANSWER_PATTERNS = [
    r"cannot\s+find\b",
    r"could\s+not\s+find\b",
    r"not\s+documented\b",
    r"no\s+information\s+(found|available)\b",
    r"not\s+available\s+in\s+the\s+docs\b",
    r"does\s+not\s+(mention|contain|provide)\b",
    r"is\s+not\s+a\s+valid\b",
    r"is\s+documented\s+as\s+a\s+blockchain.*not\s+a\b",
]


class PharosMCPError(Exception):
    """Raised when an MCP protocol, JSON-RPC, or server error occurs."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"MCP Error [{code}]: {message}")
        self.code = code
        self.message = message
        self.data = data


class PharosDocsMCPClient:
    """Official client and wrapper for the Pharos Developer Docs MCP server."""

    def __init__(
        self,
        endpoint: str = DEFAULT_DOCS_MCP_ENDPOINT,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.endpoint = endpoint
        self.user_agent = user_agent
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.server_info: Optional[Dict[str, Any]] = None
        self.server_capabilities: Optional[Dict[str, Any]] = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    @staticmethod
    def _parse_mcp_response(raw_body: str) -> Dict[str, Any]:
        """
        Parses MCP server responses, safely handling both SSE message framing
        (event: message\\ndata: {...}) and plain JSON-RPC responses.
        """
        trimmed = raw_body.strip()
        if not trimmed:
            raise PharosMCPError(code=-32700, message="Empty response body from Docs MCP server.")

        data_payloads = []
        for line in trimmed.splitlines():
            line_str = line.strip()
            if line_str.startswith("data:"):
                payload = line_str[5:].strip()
                if payload:
                    data_payloads.append(payload)

        if data_payloads:
            try:
                return json.loads(data_payloads[-1])
            except json.JSONDecodeError as e:
                raise PharosMCPError(code=-32700, message=f"Malformed SSE JSON payload: {e}")

        try:
            return json.loads(trimmed)
        except json.JSONDecodeError as e:
            raise PharosMCPError(code=-32700, message=f"Malformed JSON-RPC response: {e}")

    def _rpc_call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        is_notification: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a JSON-RPC 2.0 call against the Streamable HTTP MCP server.
        """
        call_id = None if is_notification else self._next_id()
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method
        }
        if call_id is not None:
            payload["id"] = call_id
        if params is not None:
            payload["params"] = params

        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": self.user_agent
        }
        if self.session_id:
            req_headers["mcp-session-id"] = self.session_id

        req_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=req_bytes,
            headers=req_headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                new_session = resp.headers.get("mcp-session-id")
                if new_session:
                    self.session_id = new_session

                raw_bytes = resp.read()
                if not raw_bytes or is_notification:
                    return None

                body_text = raw_bytes.decode("utf-8", errors="replace")
                data = self._parse_mcp_response(body_text)

                if "error" in data:
                    err = data["error"]
                    raise PharosMCPError(
                        code=err.get("code", -32000),
                        message=err.get("message", "Unknown MCP server error"),
                        data=err.get("data")
                    )

                return data
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise PharosMCPError(
                code=e.code,
                message=f"HTTP {e.code}: {e.reason}. {err_body[:200]}"
            )
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to Docs MCP at {self.endpoint}: {e.reason}")
        except TimeoutError as e:
            raise TimeoutError(f"Docs MCP request timed out after {self.timeout}s: {e}")

    def initialize(self) -> Dict[str, Any]:
        """
        Initializes the MCP session with the server and exchanges capabilities.
        """
        params = {
            "protocolVersion": DEFAULT_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "pharos-doc-search-cli",
                "version": "2.0.0"
            }
        }
        resp = self._rpc_call("initialize", params)
        if not resp or "result" not in resp:
            raise PharosMCPError(code=-32603, message=f"Malformed initialize response: {resp}")

        result = resp["result"]
        self.server_info = result.get("serverInfo", {})
        self.server_capabilities = result.get("capabilities", {})

        # Send notifications/initialized as required by MCP protocol specification
        try:
            self._rpc_call("notifications/initialized", {}, is_notification=True)
        except Exception:
            pass

        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Discovers all available documentation tools from the server via tools/list.
        """
        if not self.server_info:
            self.initialize()

        resp = self._rpc_call("tools/list", {})
        if not resp or "result" not in resp:
            raise PharosMCPError(code=-32603, message=f"Malformed tools/list response: {resp}")

        return resp["result"].get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes an MCP tool on the server via tools/call.
        """
        if not tool_name or not tool_name.strip():
            raise ValueError("Tool name cannot be empty.")
        if not self.server_info:
            self.initialize()

        params = {
            "name": tool_name.strip(),
            "arguments": arguments
        }
        resp = self._rpc_call("tools/call", params)
        if not resp or "result" not in resp:
            raise PharosMCPError(code=-32603, message=f"Malformed tools/call response: {resp}")

        return resp["result"]

    def parse_markdown_response(
        self,
        raw_markdown: str,
        query: str
    ) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], bool]:
        """
        Parses raw MCP markdown output into clean components:
        - Concise answer
        - Sourced doc sections (with absolute URLs resolved)
        - Suggested follow-up questions
        - has_answer flag (True if relevant answer found, False if no good answer)
        """
        if not raw_markdown or not raw_markdown.strip():
            return "", [], [], False

        content = raw_markdown.strip()

        # Extract Sources block
        sources: List[Dict[str, str]] = []
        sources_match = re.search(r"#+\s*Sources:?\s*(.*)", content, re.DOTALL | re.IGNORECASE)
        if sources_match:
            sources_block = sources_match.group(1)
            for m in re.finditer(r"-\s*\[(.*?)\]\((.*?)\)", sources_block):
                title = m.group(1).strip()
                link = m.group(2).strip()
                if link.startswith("/"):
                    link = f"{DOCS_BASE_URL}{link}"
                sources.append({"title": title, "url": link})

        # Extract Suggested Follow-up Questions block
        follow_ups: List[Dict[str, str]] = []
        followups_match = re.search(
            r"#+\s*Suggested Follow-up Questions:?\s*(.*?)(?=#+\s*Sources:?|$)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if followups_match:
            followups_block = followups_match.group(1)
            for m in re.finditer(r"-\s*\[(.*?)\]\((.*?)\)", followups_block):
                q_text = m.group(1).strip()
                q_url = m.group(2).strip()
                if q_url.startswith("/"):
                    q_url = f"{DOCS_BASE_URL}{q_url}"
                follow_ups.append({"question": q_text, "url": q_url})

        # Main answer text is everything before Suggested Follow-ups or Sources
        cutoff_match = re.search(r"#+\s*(Suggested Follow-up Questions|Sources):?", content, re.IGNORECASE)
        if cutoff_match:
            answer_text = content[:cutoff_match.start()].strip()
        else:
            answer_text = content

        # Strip heading # <Question>? if repeated at top
        answer_text = re.sub(r"^#+\s*.*?\n+", "", answer_text).strip()

        # Resolve any internal relative links inside the answer text to full URLs
        def _resolve_link(match):
            text = match.group(1)
            url = match.group(2)
            if url.startswith("/"):
                url = f"{DOCS_BASE_URL}{url}"
            return f"[{text}]({url})"

        answer_text = re.sub(r"\[([^\]]+)\]\((/[^\)]+)\)", _resolve_link, answer_text)

        # Evaluate if answer represents "no good answer found"
        has_answer = True
        lower_ans = answer_text.lower()

        if len(answer_text) < 15:
            has_answer = False
        else:
            for pattern in NO_ANSWER_PATTERNS:
                if re.search(pattern, lower_ans):
                    has_answer = False
                    break

        return answer_text, sources, follow_ups, has_answer

    def ask_question(self, question: str, goal: Optional[str] = None) -> Dict[str, Any]:
        """Invokes official `askQuestion` MCP tool."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        args: Dict[str, Any] = {"question": question.strip()}
        if goal and goal.strip():
            args["goal"] = goal.strip()

        start = time.time()
        tool_res = self.call_tool("askQuestion", args)
        elapsed = round(time.time() - start, 2)

        content_items = tool_res.get("content", [])
        raw_text = "\n\n".join(item.get("text", "") for item in content_items if item.get("type") == "text")
        answer, sources, follow_ups, has_answer = self.parse_markdown_response(raw_text, question)

        return {
            "success": True,
            "tool": "askQuestion",
            "query": question.strip(),
            "goal": goal or DEFAULT_GOAL,
            "endpoint": self.endpoint,
            "server_info": self.server_info,
            "http_status": 200,
            "elapsed_seconds": elapsed,
            "answer": answer,
            "has_answer": has_answer,
            "sources": sources,
            "follow_ups": follow_ups,
            "raw_markdown": raw_text,
            "error": None,
        }

    def search_documentation(self, query: str) -> Dict[str, Any]:
        """Invokes official `searchDocumentation` MCP tool."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        start = time.time()
        tool_res = self.call_tool("searchDocumentation", {"query": query.strip()})
        elapsed = round(time.time() - start, 2)

        content_items = tool_res.get("content", [])
        raw_text = "\n\n".join(item.get("text", "") for item in content_items if item.get("type") == "text")

        # Parse search chunks into structured sources
        sources: List[Dict[str, str]] = []
        for chunk in content_items:
            t = chunk.get("text", "")
            title_m = re.search(r"Title:\s*(.+)", t)
            link_m = re.search(r"Link:\s*(.+)", t)
            if title_m and link_m:
                sources.append({
                    "title": title_m.group(1).strip(),
                    "url": link_m.group(1).strip()
                })

        has_answer = len(content_items) > 0

        return {
            "success": True,
            "tool": "searchDocumentation",
            "query": query.strip(),
            "goal": DEFAULT_GOAL,
            "endpoint": self.endpoint,
            "server_info": self.server_info,
            "http_status": 200,
            "elapsed_seconds": elapsed,
            "answer": raw_text if has_answer else "No matching documentation found.",
            "has_answer": has_answer,
            "sources": sources,
            "follow_ups": [],
            "raw_markdown": raw_text,
            "error": None,
        }

    def get_page(self, url: str) -> Dict[str, Any]:
        """Invokes official `getPage` MCP tool."""
        if not url or not url.strip():
            raise ValueError("Page URL cannot be empty.")

        start = time.time()
        tool_res = self.call_tool("getPage", {"url": url.strip()})
        elapsed = round(time.time() - start, 2)

        content_items = tool_res.get("content", [])
        raw_text = "\n\n".join(item.get("text", "") for item in content_items if item.get("type") == "text")

        return {
            "success": True,
            "tool": "getPage",
            "url": url.strip(),
            "endpoint": self.endpoint,
            "server_info": self.server_info,
            "http_status": 200,
            "elapsed_seconds": elapsed,
            "answer": raw_text,
            "has_answer": len(raw_text.strip()) > 0,
            "sources": [{"title": url, "url": url}],
            "follow_ups": [],
            "raw_markdown": raw_text,
            "error": None,
        }

    def query(self, ask: str, goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a documentation query via Developer Docs MCP `askQuestion` tool.
        Returns structured results matching the CLI formatting contract.
        Never reverts to GitBook HTTP ask endpoints.
        """
        clean_ask = (ask or "").strip()
        if not clean_ask:
            return {
                "success": False,
                "tool": "askQuestion",
                "query": "",
                "goal": goal or DEFAULT_GOAL,
                "endpoint": self.endpoint,
                "server_info": self.server_info,
                "http_status": 0,
                "elapsed_seconds": 0.0,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": "Query question cannot be empty.",
            }

        effective_goal = goal.strip() if goal and goal.strip() else DEFAULT_GOAL
        start_time = time.time()

        try:
            return self.ask_question(clean_ask, effective_goal)
        except PharosMCPError as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "tool": "askQuestion",
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": self.endpoint,
                "server_info": self.server_info,
                "http_status": e.code if e.code > 0 else 500,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": str(e),
            }
        except ConnectionError as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "tool": "askQuestion",
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": self.endpoint,
                "server_info": self.server_info,
                "http_status": 0,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"Network Error: {str(e)}",
            }
        except TimeoutError as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "tool": "askQuestion",
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": self.endpoint,
                "server_info": self.server_info,
                "http_status": 0,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"Timeout Error: {str(e)}",
            }
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "tool": "askQuestion",
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": self.endpoint,
                "server_info": self.server_info,
                "http_status": 0,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"Unexpected Error: {str(e)}",
            }


# Backward-compatible alias
PharosDocsClient = PharosDocsMCPClient
