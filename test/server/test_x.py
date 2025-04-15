import unittest

from server.utils.x import get_server


class TestX(unittest.TestCase):
    def test_util_x(self) -> None:
        val = get_server()
        self.assertEqual(val, "server")


if __name__ == "__main__":
    unittest.main()
