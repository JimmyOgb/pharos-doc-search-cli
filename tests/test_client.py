"""
Unit and regression tests for PharosDocsMCPClient (pharos_docs/client.py).
Tests MCP JSON-RPC protocol framing, session initialization, tool discovery,
tool invocation, error handling, source link resolution, and regression protection.
"""

import io
import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from pharos_docs.client import (
    PharosDocsMCPClient,
    PharosDocsClient,
    PharosMCPError,
    DEFAULT_DOCS_MCP_ENDPOINT,
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_GOAL,
    DOCS_BASE_URL,
)


def make_mcp_sse_response(payload: dict, status: int = 200) -> MagicMock:
    """Helper to mock an MCP Streamable HTTP response with SSE framing."""
    sse_text = f"event: message\ndata: {json.dumps(payload)}\n\n"
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.headers = {"Content-Type": "text/event-stream"}
    mock_resp.read.return_value = sse_text.encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


class TestPharosDocsClient(unittest.TestCase):
    def setUp(self):
        self.client = PharosDocsMCPClient(endpoint=DEFAULT_DOCS_MCP_ENDPOINT, timeout=10)

    def test_empty_query(self):
        result = self.client.query("")
        self.assertFalse(result["success"])
        self.assertIn("cannot be empty", result["error"])
        self.assertEqual(result["http_status"], 0)

    def test_empty_tool_arguments_raise_error(self):
        with self.assertRaises(ValueError):
            self.client.ask_question("")
        with self.assertRaises(ValueError):
            self.client.search_documentation("")
        with self.assertRaises(ValueError):
            self.client.get_page("")
        with self.assertRaises(ValueError):
            self.client.call_tool("", {})

    @patch("urllib.request.urlopen")
    def test_mcp_initialize_mock(self, mock_urlopen):
        """Verifies JSON-RPC 2.0 initialize request and capability handshake."""
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {
                    "name": "docs.pharos.xyz/~gitbook/mcp",
                    "title": "docs.pharos.xyz MCP Server",
                    "version": "0.27.2",
                },
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(init_payload)

        result = self.client.initialize()
        self.assertEqual(result["protocolVersion"], DEFAULT_PROTOCOL_VERSION)
        self.assertEqual(self.client.server_info["version"], "0.27.2")
        self.assertEqual(self.client.server_info["name"], "docs.pharos.xyz/~gitbook/mcp")

        # Verify outgoing request was POST to MCP endpoint with initialize method
        self.assertGreaterEqual(len(mock_urlopen.call_args_list), 1)
        req = mock_urlopen.call_args_list[0][0][0]
        self.assertEqual(req.full_url, DEFAULT_DOCS_MCP_ENDPOINT)
        self.assertEqual(req.get_method(), "POST")
        sent_body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(sent_body["method"], "initialize")
        self.assertEqual(sent_body["params"]["protocolVersion"], DEFAULT_PROTOCOL_VERSION)

    @patch("urllib.request.urlopen")
    def test_mcp_list_tools_mock(self, mock_urlopen):
        """Verifies tools/list schema discovery."""
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        tools_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "searchDocumentation", "description": "Search docs"},
                    {"name": "getPage", "description": "Get page content"},
                    {"name": "askQuestion", "description": "Ask question"},
                    {"name": "sendFeedback", "description": "Report doc issue"},
                ]
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(tools_payload)

        tools = self.client.list_tools()
        self.assertEqual(len(tools), 4)
        tool_names = [t["name"] for t in tools]
        self.assertIn("askQuestion", tool_names)
        self.assertIn("searchDocumentation", tool_names)
        self.assertIn("getPage", tool_names)
        self.assertIn("sendFeedback", tool_names)

    @patch("urllib.request.urlopen")
    def test_mcp_ask_question_mock(self, mock_urlopen):
        """Verifies tools/call for askQuestion tool."""
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        call_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Deploy using Foundry scripts. See [Write Your First Token](/developer-guide/foundry/write-your-first-token.md).\n\n"
                            "# Sources\n\n"
                            "- [Foundry Guide](https://docs.pharos.xyz/developer-guide/foundry.md)\n"
                        ),
                    }
                ]
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(call_payload)

        res = self.client.ask_question("How do I deploy a contract?", goal="test goal")
        self.assertTrue(res["success"])
        self.assertEqual(res["tool"], "askQuestion")
        self.assertIn("Deploy using Foundry scripts", res["answer"])
        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["title"], "Foundry Guide")
        self.assertEqual(res["sources"][0]["url"], "https://docs.pharos.xyz/developer-guide/foundry.md")

    @patch("urllib.request.urlopen")
    def test_mcp_search_documentation_mock(self, mock_urlopen):
        """Verifies tools/call for searchDocumentation tool."""
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        search_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Title: Atlantic Testnet\nLink: https://docs.pharos.xyz/getting-started/network/atlantic-testnet\nContent: RPC URL",
                    }
                ]
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(search_payload)

        res = self.client.search_documentation("Atlantic RPC")
        self.assertTrue(res["success"])
        self.assertEqual(res["tool"], "searchDocumentation")
        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["title"], "Atlantic Testnet")
        self.assertEqual(res["sources"][0]["url"], "https://docs.pharos.xyz/getting-started/network/atlantic-testnet")

    @patch("urllib.request.urlopen")
    def test_mcp_get_page_mock(self, mock_urlopen):
        """Verifies tools/call for getPage tool."""
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        page_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "# Atlantic Testnet\n\nFull page markdown documentation content.",
                    }
                ]
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(page_payload)

        res = self.client.get_page("https://docs.pharos.xyz/getting-started/network/atlantic-testnet")
        self.assertTrue(res["success"])
        self.assertEqual(res["tool"], "getPage")
        self.assertIn("# Atlantic Testnet", res["answer"])

    def test_parse_successful_response_with_sources_and_followups(self):
        sample_markdown = """# How do I deploy a contract?

Deploy using Foundry scripts or Hardhat Ignition. See [Write Your First Token](/developer-guide/foundry/write-your-first-token.md).

# Suggested Follow-up Questions:

If you need more information, consider asking one of these follow-up questions:

- [Which Pharos RPC URL to use?](/tooling-and-infrastructure/rpc.md)
- [How to verify a contract on SocialScan?](/tooling-and-infrastructure/verification.md)

# Sources:

- [Foundry Guide](https://docs.pharos.xyz/developer-guide/foundry.md)
- [Hardhat Guide](/developer-guide/hardhat.md)
"""
        answer, sources, follow_ups, has_answer = self.client.parse_markdown_response(
            sample_markdown, "How do I deploy a contract?"
        )

        self.assertTrue(has_answer)
        self.assertIn("Deploy using Foundry scripts", answer)
        self.assertIn("https://docs.pharos.xyz/developer-guide/foundry/write-your-first-token.md", answer)
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["title"], "Foundry Guide")
        self.assertEqual(sources[0]["url"], "https://docs.pharos.xyz/developer-guide/foundry.md")
        self.assertEqual(sources[1]["title"], "Hardhat Guide")
        self.assertEqual(sources[1]["url"], f"{DOCS_BASE_URL}/developer-guide/hardhat.md")
        self.assertEqual(len(follow_ups), 2)
        self.assertEqual(follow_ups[0]["question"], "Which Pharos RPC URL to use?")

    def test_no_good_answer_found_detection(self):
        cookie_markdown = """# What is the recipe for baking chocolate chip cookies on Pharos?

I cannot find a chocolate chip cookie recipe in the docs. Pharos is documented as a blockchain network, not a baking service. See [About Pharos](/introduction/readme.md).

# Sources:

- [About Pharos](https://docs.pharos.xyz/introduction/readme.md)
"""
        answer, sources, follow_ups, has_answer = self.client.parse_markdown_response(
            cookie_markdown, "cookie recipe"
        )
        self.assertFalse(has_answer)
        self.assertIn("cannot find a chocolate chip cookie recipe", answer)
        self.assertEqual(len(sources), 1)

    def test_no_information_pattern_detection(self):
        sample = "There is no information available in the docs for quantum teleportation."
        answer, sources, follow_ups, has_answer = self.client.parse_markdown_response(
            sample, "quantum teleportation"
        )
        self.assertFalse(has_answer)

    def test_empty_or_too_short_response(self):
        answer, sources, follow_ups, has_answer = self.client.parse_markdown_response(
            "Short", "some query"
        )
        self.assertFalse(has_answer)

    @patch("urllib.request.urlopen")
    def test_query_mcp_success(self, mock_urlopen):
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        mock_resp_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Pharos Atlantic chain ID is 688689.\n\n# Sources\n\n- [Networks](https://docs.pharos.xyz/networks.md)",
                    }
                ]
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(mock_resp_payload)

        res = self.client.query("What is chain ID?")
        self.assertTrue(res["success"])
        self.assertTrue(res["has_answer"])
        self.assertEqual(res["http_status"], 200)
        self.assertIn("688689", res["answer"])
        self.assertEqual(len(res["sources"]), 1)
        self.assertIsNone(res["error"])

    @patch("urllib.request.urlopen")
    def test_query_http_error(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url=DEFAULT_DOCS_MCP_ENDPOINT,
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b"Endpoint Not Found"),
        )
        mock_urlopen.side_effect = err

        res = self.client.query("Invalid endpoint query")
        self.assertFalse(res["success"])
        self.assertEqual(res["http_status"], 404)
        self.assertIn("HTTP 404", res["error"])

    @patch("urllib.request.urlopen")
    def test_query_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        res = self.client.query("Any query")
        self.assertFalse(res["success"])
        self.assertEqual(res["http_status"], 0)
        self.assertIn("Network Error", res["error"])

    @patch("urllib.request.urlopen")
    def test_query_timeout_error(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Request timed out")

        res = self.client.query("Timeout query")
        self.assertFalse(res["success"])
        self.assertEqual(res["http_status"], 0)
        self.assertIn("Timeout Error", res["error"])

    @patch("urllib.request.urlopen")
    def test_query_mcp_protocol_error(self, mock_urlopen):
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        err_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32602,
                "message": "Tool askQuestion parameter error",
            },
        }
        mock_urlopen.return_value = make_mcp_sse_response(err_payload)

        res = self.client.query("Trigger error")
        self.assertFalse(res["success"])
        self.assertIn("MCP Error", res["error"])

    @patch("urllib.request.urlopen")
    def test_regression_old_gitbook_ask_not_used(self, mock_urlopen):
        """
        REGRESSION TEST: Ensures that the implementation NEVER makes requests to
        the rejected GitBook ask endpoint (https://docs.pharos.xyz/index.md?ask=...)
        and strictly communicates via POST JSON-RPC to the Developer Docs MCP endpoint.
        """
        self.client.server_info = {"name": "docs.pharos.xyz/~gitbook/mcp"}
        mock_urlopen.return_value = make_mcp_sse_response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": "Genuine MCP Answer\n\n# Sources\n\n- [Ref](https://docs.pharos.xyz)"}]
            }
        })

        res = self.client.query("What is Atlantic RPC?")
        self.assertTrue(res["success"])

        # Inspect all calls to urlopen
        for call_item in mock_urlopen.call_args_list:
            req = call_item[0][0]
            # 1. Target URL must be the Docs MCP endpoint, NEVER index.md
            self.assertEqual(req.full_url, DEFAULT_DOCS_MCP_ENDPOINT)
            self.assertNotIn("index.md", req.full_url)
            self.assertNotIn("?ask=", req.full_url)
            # 2. Method must be POST (JSON-RPC), NEVER GET
            self.assertEqual(req.get_method(), "POST")
            # 3. Payload must be JSON-RPC MCP structure
            body = json.loads(req.data.decode("utf-8"))
            self.assertEqual(body.get("jsonrpc"), "2.0")
            self.assertEqual(body.get("method"), "tools/call")


if __name__ == "__main__":
    unittest.main()
