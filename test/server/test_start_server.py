import sys
import unittest
from unittest import mock

from server.start_server import main  # Import the main function from start_server.py


class TestServerMain(unittest.TestCase):
    @mock.patch("server.start_server.Server")  # Patch Server class
    def test_main_with_arguments(self, mock_server_class: mock.MagicMock) -> None:
        # Arrange
        test_args = [
            "start_server.py",
            "-H",
            "127.0.0.1",
            "-p",
            "8080",
            "-s",
            "/tmp",
            "-n",
            "testfile.txt",
            "-r",
            "GBN",
        ]
        with mock.patch.object(sys, "argv", test_args):
            mock_server_instance = mock_server_class.return_value

            # Act
            main()

            # Assert
            mock_server_class.assert_called_once()  # Server should be instantiated
            mock_server_instance.run.assert_called_once()  # run should be called

    @mock.patch("server.start_server.Server")
    def test_main_missing_required_argument(
        self, mock_server_class: mock.MagicMock
    ) -> None:
        # Arrange
        test_args = [
            "start_server.py",
            "-p",
            "8080",
            "-s",
            "/tmp",
            "-n",
            "testfile.txt",
        ]  # Missing -H (host)

        with mock.patch.object(sys, "argv", test_args):
            # Act + Assert
            with self.assertRaises(SystemExit):
                main()
            mock_server_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
