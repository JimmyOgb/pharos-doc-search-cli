"""
Live Integration Tests against the official Pharos Developer Docs endpoint.
Tests real network latency, response parsing, and live endpoint behavior.
"""

import unittest
import os
from pharos_docs.client import PharosDocsClient

# Can be enabled with RUN_LIVE_TESTS=1
SKIP_LIVE = os.environ.get("RUN_LIVE_TESTS", "0") != "1"


@unittest.skipIf(SKIP_LIVE, "Skipping live tests by default. Set RUN_LIVE_TESTS=1 to run.")
class TestLiveDocsIntegration(unittest.TestCase):

    def setUp(self):
        self.client = PharosDocsClient(timeout=40)

    def test_live_contract_deployment_query(self):
        result = self.client.query("How do I deploy a contract?")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_answer"])
        self.assertEqual(result["http_status"], 200)
        self.assertGreater(len(result["sources"]), 0)
        self.assertIn("Foundry", result["answer"])

    def test_live_network_query(self):
        result = self.client.query("What is the Atlantic testnet RPC URL and chain ID?")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_answer"])
        self.assertEqual(result["http_status"], 200)
        self.assertIn("688689", result["answer"])

    def test_live_irrelevant_query_handling(self):
        result = self.client.query("What is the recipe for baking chocolate chip cookies on Pharos?")
        self.assertTrue(result["success"])
        # Should gracefully recognize there is no real answer
        self.assertFalse(result["has_answer"])
        self.assertIn("cannot find", result["answer"].lower())


if __name__ == "__main__":
    unittest.main()
