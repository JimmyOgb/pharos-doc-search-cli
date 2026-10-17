import unittest
from unittest.mock import patch, MagicMock
import json
import io
import sys

from pharos_docs.cli import main, format_terminal_output


class TestPharosDocsCLI(unittest.TestCase):

    def test_format_terminal_output_success(self):
        result = {
            "query": "How do I deploy?",
            "elapsed_seconds": 12.34,
            "http_status": 200,
            "has_answer": True,
            "answer": "Use forge script.",
            "sources": [{"title": "Deploy Guide", "url": "https://docs.pharos.xyz/deploy.md"}],
            "follow_ups": [{"question": "What RPC to use?", "url": "https://docs.pharos.xyz"}]
        }
        output = format_terminal_output(result, no_color=True)
        self.assertIn("=== Pharos Developer Docs Search ===", output)
        self.assertIn("Query: \"How do I deploy?\"", output)
        self.assertIn("[Answer]", output)
        self.assertIn("Use forge script.", output)
        self.assertIn("[Sources & Documentation References]", output)
        self.assertIn("Deploy Guide", output)
        self.assertIn("-> https://docs.pharos.xyz/deploy.md", output)
        self.assertIn("[Suggested Follow-Up Queries]", output)
        self.assertIn("* What RPC to use?", output)

    def test_format_terminal_output_no_answer(self):
        result = {
            "query": "cookie recipe",
            "elapsed_seconds": 9.5,
            "http_status": 200,
            "has_answer": False,
            "answer": "I cannot find a chocolate chip cookie recipe in the docs.",
            "sources": [{"title": "About Pharos", "url": "https://docs.pharos.xyz/about.md"}],
            "follow_ups": []
        }
        output = format_terminal_output(result, no_color=True)
        self.assertIn("[Notice: No Good Answer Found in Official Docs]", output)
        self.assertIn("I cannot find a chocolate chip cookie recipe in the docs.", output)

    @patch("pharos_docs.client.PharosDocsClient.query")
    def test_cli_success_exit_code_and_output(self, mock_query):
        mock_query.return_value = {
            "success": True,
            "query": "How to deploy?",
            "goal": "deploy",
            "endpoint": "https://docs.pharos.xyz/index.md",
            "http_status": 200,
            "elapsed_seconds": 5.0,
            "answer": "Deploy with Foundry.",
            "has_answer": True,
            "sources": [{"title": "Guide", "url": "https://docs.pharos.xyz/guide"}],
            "follow_ups": [],
            "raw_markdown": "Deploy with Foundry.",
            "error": None
        }

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            exit_code = main(["How to deploy?", "--no-color"])

        self.assertEqual(exit_code, 0)
        output = captured_stdout.getvalue()
        self.assertIn("Deploy with Foundry.", output)

    @patch("pharos_docs.client.PharosDocsClient.query")
    def test_cli_json_output(self, mock_query):
        mock_query.return_value = {
            "success": True,
            "query": "What is chain ID?",
            "goal": "test",
            "endpoint": "https://docs.pharos.xyz/index.md",
            "http_status": 200,
            "elapsed_seconds": 3.2,
            "answer": "688689",
            "has_answer": True,
            "sources": [],
            "follow_ups": [],
            "raw_markdown": "688689",
            "error": None
        }

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            exit_code = main(["What is chain ID?", "--json"])

        self.assertEqual(exit_code, 0)
        data = json.loads(captured_stdout.getvalue())
        self.assertEqual(data["answer"], "688689")
        self.assertTrue(data["has_answer"])

    @patch("pharos_docs.client.PharosDocsClient.query")
    def test_cli_no_answer_exit_code(self, mock_query):
        mock_query.return_value = {
            "success": True,
            "query": "baking cookies",
            "goal": "test",
            "endpoint": "https://docs.pharos.xyz/index.md",
            "http_status": 200,
            "elapsed_seconds": 4.1,
            "answer": "cannot find a cookie recipe",
            "has_answer": False,
            "sources": [],
            "follow_ups": [],
            "raw_markdown": "cannot find a cookie recipe",
            "error": None
        }

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            exit_code = main(["baking cookies", "--no-color"])

        # Returns 2 to indicate "no answer found"
        self.assertEqual(exit_code, 2)
        self.assertIn("Notice: No Good Answer Found", captured_stdout.getvalue())

    @patch("pharos_docs.client.PharosDocsClient.query")
    def test_cli_error_exit_code(self, mock_query):
        mock_query.return_value = {
            "success": False,
            "query": "test query",
            "goal": "test",
            "endpoint": "https://docs.pharos.xyz/index.md",
            "http_status": 500,
            "elapsed_seconds": 1.0,
            "answer": "",
            "has_answer": False,
            "sources": [],
            "follow_ups": [],
            "raw_markdown": "",
            "error": "HTTP 500: Internal Server Error"
        }

        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            exit_code = main(["test query"])

        self.assertEqual(exit_code, 1)
        self.assertIn("HTTP 500", captured_stderr.getvalue())

    def test_cli_empty_args(self):
        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            exit_code = main([])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
