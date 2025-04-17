import sys
import unittest
from argparse import Namespace
from io import StringIO

from client.utils.client import Client


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        # This runs before each test
        self.args = Namespace(
            host="localhost",
            port=8080,
            dst="test/path",
            name="file.txt",
            protocol="tcp",
            verbose=False,
            quiet=False,
        )
        self.client = Client(self.args)

    def test_client_initialization(self) -> None:
        self.assertEqual(self.client.host, "localhost")
        self.assertEqual(self.client.port, 8080)
        self.assertEqual(self.client.dst, "test/path")
        self.assertEqual(self.client.name, "file.txt")
        self.assertEqual(self.client.protocol, "tcp")
        self.assertFalse(self.client.verbose)
        self.assertFalse(self.client.quiet)

    def test_handle_download_normal(self) -> None:
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_download()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Downloading file...", output)
        self.assertIn("Download complete.", output)

    def test_handle_download_verbose(self) -> None:
        self.client.verbose = True
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_download()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Starting download with the following parameters:", output)
        self.assertIn("Host: localhost", output)
        self.assertIn("Port: 8080", output)
        self.assertIn("Destination Path: test/path", output)
        self.assertIn("Download complete.", output)

    def test_handle_download_quiet(self) -> None:
        self.client.quiet = True
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_download()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        # In quiet mode, should only see "Download complete."
        self.assertNotIn("Downloading file...", output)
        self.assertIn("Download complete.", output)

    def test_handle_upload_normal(self) -> None:
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_upload()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Uploading file...", output)

    def test_handle_upload_verbose(self) -> None:
        self.client.verbose = True
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_upload()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Starting upload with the following parameters:", output)
        self.assertIn("Host: localhost", output)
        self.assertIn("Source Path: test/path", output)

    def test_handle_upload_quiet(self) -> None:
        self.client.quiet = True
        captured_output = StringIO()
        sys.stdout = captured_output
        self.client.handle_upload()
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertEqual(output, "")  # Should produce no output


if __name__ == "__main__":
    unittest.main()
