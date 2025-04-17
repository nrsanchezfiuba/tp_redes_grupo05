import unittest
from argparse import Namespace
from unittest import mock

from server.utils.server import Server


class TestServer(unittest.TestCase):
    def setUp(self) -> None:
        # Default arguments for tests
        self.args = Namespace(
            host="127.0.0.1",
            port=8080,
            storage="/tmp",
            name="testfile.txt",
            protocol="GBN",
            verbose=False,
            quiet=False,
        )

    @mock.patch("builtins.print")
    def test_run_verbose(self, mock_print: mock.MagicMock) -> None:
        self.args.verbose = True
        server = Server(self.args)

        server.run()

        self.assertTrue(mock_print.called)
        expected_calls = [
            mock.call("Starting server with the following parameters:"),
            mock.call(f"Host: {server.host}"),
            mock.call(f"Port: {server.port}"),
            mock.call(f"storage folder dir path: {server.storage}"),
            mock.call(f"File Name: {server.name}"),
            mock.call(f"Protocol: {server.protocol}"),
        ]
        mock_print.assert_has_calls(expected_calls, any_order=False)

    @mock.patch("builtins.print")
    def test_run_quiet(self, mock_print: mock.MagicMock) -> None:
        self.args.quiet = True
        server = Server(self.args)

        server.run()

        mock_print.assert_not_called()

    @mock.patch("builtins.print")
    def test_run_default(self, mock_print: mock.MagicMock) -> None:
        server = Server(self.args)

        server.run()

        mock_print.assert_called_once_with("Start Server...")

    def test_server_initialization(self) -> None:
        server = Server(self.args)

        self.assertEqual(server.host, "127.0.0.1")
        self.assertEqual(server.port, 8080)
        self.assertEqual(server.storage, "/tmp")
        self.assertEqual(server.name, "testfile.txt")
        self.assertEqual(server.protocol, "GBN")
        self.assertFalse(server.verbose)
        self.assertFalse(server.quiet)


if __name__ == "__main__":
    unittest.main()
