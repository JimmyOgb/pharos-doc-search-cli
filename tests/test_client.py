import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import io

from pharos_docs.client import (
    PharosDocsClient,
    DEFAULT_DOCS_ENDPOINT,
    DEFAULT_GOAL,
    DOCS_BASE_URL,
)


class TestPharosDocsClient(unittest.TestCase):
    def setUp(self):
        self.client = PharosDocsClient(endpoint=DEFAULT_DOCS_ENDPOINT, timeout=10)

    def test_build_query_url(self):
        url = self.client.build_query_url("How do I deploy?", "custom goal")
        self.assertTrue(url.startswith(DEFAULT_DOCS_ENDPOINT))
        self.assertIn("ask=How+do+I+deploy%3F", url)
        self.assertIn("goal=custom+goal", url)

    def test_empty_query(self):
        result = self.client.query("")
        self.assertFalse(result["success"])
        self.assertIn("cannot be empty", result["error"])
        self.assertEqual(result["http_status"], 0)

    def test_parse_successful_response_with_sources_and_followups(self):
        sample_markdown = """# How do I deploy a contract?

Deploy using Foundry scripts or Hardhat Ignition. See [Write Your First Token](/developer-guide/foundry/write-your-first-token.md).

# Suggested Follow-up Questions:

If you need more information, consider asking one of these follow-up questions by performing an HTTP GET request on the URL:

- [Which Pharos RPC URL to use?](https://docs.pharos.xyz?ask=Which%20Pharos%20RPC%20URL%20to%20use%3F)
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
        # Verify internal link resolution
        self.assertIn("https://docs.pharos.xyz/developer-guide/foundry/write-your-first-token.md", answer)

        # Verify sources extraction
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["title"], "Foundry Guide")
        self.assertEqual(sources[0]["url"], "https://docs.pharos.xyz/developer-guide/foundry.md")
        self.assertEqual(sources[1]["title"], "Hardhat Guide")
        self.assertEqual(sources[1]["url"], f"{DOCS_BASE_URL}/developer-guide/hardhat.md")

        # Verify follow-ups
        self.assertEqual(len(follow_ups), 2)
        self.assertEqual(follow_ups[0]["question"], "Which Pharos RPC URL to use?")
        self.assertEqual(follow_ups[1]["url"], f"{DOCS_BASE_URL}/tooling-and-infrastructure/verification.md")

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
    def test_query_http_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"# Heading\n\nPharos Atlantic chain ID is 688689.\n\n# Sources:\n\n- [Networks](https://docs.pharos.xyz/networks.md)"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

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
            url="https://docs.pharos.xyz",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b"Page Not Found")
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
    def test_malformed_response_handling(self, mock_urlopen):
        # Bytes that don't match standard template
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"Plain unformatted response without headers or sources."
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.client.query("Any query")
        self.assertTrue(res["success"])
        self.assertTrue(res["has_answer"])
        self.assertEqual(res["sources"], [])
        self.assertEqual(res["follow_ups"], [])
        self.assertEqual(res["answer"], "Plain unformatted response without headers or sources.")


if __name__ == "__main__":
    unittest.main()
