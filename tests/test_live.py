"""
Live Integration Tests against the official Pharos Developer Docs MCP endpoint.
Tests real network latency, JSON-RPC MCP handshake, tool discovery, and live queries.
"""

import unittest
import os
from pharos_docs.client import PharosDocsMCPClient, DEFAULT_PROTOCOL_VERSION

# Can be enabled with RUN_LIVE_TESTS=1 or PHAROS_LIVE_TESTS=1
SKIP_LIVE = (
    os.environ.get("RUN_LIVE_TESTS", "0") != "1"
    and os.environ.get("PHAROS_LIVE_TESTS", "0") != "1"
)


@unittest.skipIf(SKIP_LIVE, "Skipping live tests by default. Set RUN_LIVE_TESTS=1 to run.")
class TestLiveDocsMCPIntegration(unittest.TestCase):

    def setUp(self):
        self.client = PharosDocsMCPClient(timeout=40)

    def test_live_mcp_handshake_and_tool_discovery(self):
        init_res = self.client.initialize()
        self.assertEqual(init_res["protocolVersion"], DEFAULT_PROTOCOL_VERSION)
        self.assertIn("docs.pharos.xyz", self.client.server_info["name"])

        tools = self.client.list_tools()
        self.assertGreaterEqual(len(tools), 4)
        tool_names = [t["name"] for t in tools]
        self.assertIn("askQuestion", tool_names)
        self.assertIn("searchDocumentation", tool_names)
        self.assertIn("getPage", tool_names)
        self.assertIn("sendFeedback", tool_names)

    def test_live_contract_deployment_query(self):
        result = self.client.query("How do I deploy a contract?")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_answer"])
        self.assertEqual(result["http_status"], 200)
        self.assertGreater(len(result["sources"]), 0)
        self.assertTrue(any(k in result["answer"] for k in ["Foundry", "Hardhat", "contract"]))

    def test_live_network_query(self):
        result = self.client.query("What is the Atlantic testnet RPC URL and chain ID?")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_answer"])
        self.assertEqual(result["http_status"], 200)
        self.assertIn("688689", result["answer"])
        self.assertGreater(len(result["sources"]), 0)

    def test_live_irrelevant_query_handling(self):
        result = self.client.query("What is the recipe for baking chocolate chip cookies on Pharos?")
        self.assertTrue(result["success"])
        # Gracefully recognizes there is no real answer in official blockchain docs
        self.assertFalse(result["has_answer"])
        self.assertTrue(any(k in result["answer"].lower() for k in ["cannot find", "not found", "cookie"]))

    def test_live_search_documentation_tool(self):
        result = self.client.search_documentation("Atlantic RPC")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_answer"])
        self.assertGreater(len(result["sources"]), 0)


if __name__ == "__main__":
    unittest.main()
