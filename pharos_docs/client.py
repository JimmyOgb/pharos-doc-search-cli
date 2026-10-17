"""
Pharos Developer Docs MCP Client
Implements the official GitBook dynamic agentic query protocol for Pharos documentation.

Protocol Reference:
    GET https://docs.pharos.xyz/index.md?ask=<question>&goal=<user_goal>

Features:
    - 100% Python Standard Library (urllib, re, json, time).
    - Zero external dependencies.
    - Zero cost ($0.00).
    - Source link extraction & resolution.
    - Honest "No Good Answer Found" detection.
"""

import re
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_DOCS_ENDPOINT = "https://docs.pharos.xyz/index.md"
DOCS_BASE_URL = "https://docs.pharos.xyz"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PharosDocSearchCLI/1.0 (+https://github.com/JimmyOgb/pharos-doc-search-cli)"
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


class PharosDocsClient:
    """Client for querying the official Pharos Developer Docs agentic interface."""

    def __init__(
        self,
        endpoint: str = DEFAULT_DOCS_ENDPOINT,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.endpoint = endpoint
        self.user_agent = user_agent
        self.timeout = timeout

    def build_query_url(self, ask: str, goal: Optional[str] = None) -> str:
        """Constructs canonical query URL with encoded parameters."""
        effective_goal = goal.strip() if goal else DEFAULT_GOAL
        params = urllib.parse.urlencode({
            "ask": ask.strip(),
            "goal": effective_goal,
        })
        base = self.endpoint.split("?")[0]
        return f"{base}?{params}"

    def parse_markdown_response(
        self,
        raw_markdown: str,
        query: str
    ) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], bool]:
        """
        Parses raw GitBook agentic markdown output into clean components:
        - Concise answer
        - Sourced doc sections (with absolute URLs)
        - Suggested follow-up questions
        - has_answer flag (True if relevant answer found, False if no good answer)
        """
        if not raw_markdown or not raw_markdown.strip():
            return "", [], [], False

        # Split into main answer, follow-ups, and sources
        content = raw_markdown.strip()

        # Extract Sources block
        sources: List[Dict[str, str]] = []
        sources_match = re.search(r"#+\s*Sources:\s*(.*)", content, re.DOTALL | re.IGNORECASE)
        if sources_match:
            sources_block = sources_match.group(1)
            # Find markdown links: [Title](url)
            for m in re.finditer(r"-\s*\[(.*?)\]\((.*?)\)", sources_block):
                title = m.group(1).strip()
                link = m.group(2).strip()
                if link.startswith("/"):
                    link = f"{DOCS_BASE_URL}{link}"
                sources.append({"title": title, "url": link})

        # Extract Suggested Follow-up Questions block
        follow_ups: List[Dict[str, str]] = []
        followups_match = re.search(
            r"#+\s*Suggested Follow-up Questions:\s*(.*?)(?=#+\s*Sources:|$)",
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
        cutoff_match = re.search(r"#+\s*(Suggested Follow-up Questions|Sources):", content, re.IGNORECASE)
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

    def query(self, ask: str, goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a dynamic documentation query and returns structured results.

        Returns:
            Dict containing:
                success: bool
                query: str
                goal: str
                endpoint: str
                http_status: int
                elapsed_seconds: float
                answer: str
                has_answer: bool
                sources: List[Dict[str, str]]
                follow_ups: List[Dict[str, str]]
                raw_markdown: str
                error: Optional[str]
        """
        clean_ask = (ask or "").strip()
        if not clean_ask:
            return {
                "success": False,
                "query": "",
                "goal": goal or DEFAULT_GOAL,
                "endpoint": self.endpoint,
                "http_status": 0,
                "elapsed_seconds": 0.0,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": "Query question cannot be empty.",
            }

        effective_goal = goal.strip() if goal else DEFAULT_GOAL
        query_url = self.build_query_url(clean_ask, effective_goal)
        start_time = time.time()

        req = urllib.request.Request(
            query_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/markdown, text/plain, application/json",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_bytes = resp.read()
                elapsed = round(time.time() - start_time, 2)
                raw_markdown = raw_bytes.decode("utf-8", errors="replace")

                answer, sources, follow_ups, has_answer = self.parse_markdown_response(
                    raw_markdown, clean_ask
                )

                return {
                    "success": True,
                    "query": clean_ask,
                    "goal": effective_goal,
                    "endpoint": query_url,
                    "http_status": resp.status,
                    "elapsed_seconds": elapsed,
                    "answer": answer,
                    "has_answer": has_answer,
                    "sources": sources,
                    "follow_ups": follow_ups,
                    "raw_markdown": raw_markdown,
                    "error": None,
                }
        except urllib.error.HTTPError as e:
            elapsed = round(time.time() - start_time, 2)
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            return {
                "success": False,
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": query_url,
                "http_status": e.code,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"HTTP {e.code}: {e.reason}. {err_body[:150]}",
            }
        except urllib.error.URLError as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": query_url,
                "http_status": 0,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"Network Error: {e.reason}",
            }
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "query": clean_ask,
                "goal": effective_goal,
                "endpoint": query_url,
                "http_status": 0,
                "elapsed_seconds": elapsed,
                "answer": "",
                "has_answer": False,
                "sources": [],
                "follow_ups": [],
                "raw_markdown": "",
                "error": f"Unexpected Error: {str(e)}",
            }
