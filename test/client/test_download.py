import sys
import unittest
from unittest import mock

from client.download import main


class TestDownloadMain(unittest.TestCase):
    # Mock the Client class inside download.py
    @mock.patch("client.download.Client")
    def test_main_with_arguments(self, mock_client_class: mock.MagicMock) -> None:
        # Arrange
        test_args = [
            "download.py",
            "-H",
            "127.0.0.1",
            "-p",
            "8080",
            "-d",
            "/tmp",
            "-n",
            "testfile.txt",
            "-r",
            "GBN",
        ]
        with mock.patch.object(sys, "argv", test_args):
            # Act
            main()

            # Assert
            mock_client_class.assert_called_once()  # Client should be instantiated
            # handle_download should be called

    @mock.patch("client.download.Client")
    def test_main_missing_argument(self, mock_client_class: mock.MagicMock) -> None:
        # Arrange
        test_args = [
            "download.py",
            # Missing host argument
            "-p",
            "8080-d",
            "/tmp",
            "-n",
            "testfile.txt",
        ]
        with mock.patch.object(sys, "argv", test_args):
            # Act + Assert
            with self.assertRaises(SystemExit):
                main()
            mock_client_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
