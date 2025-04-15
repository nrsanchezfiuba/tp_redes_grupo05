import unittest

from client.utils.x import get_client


class TestX(unittest.TestCase):
    def test_util_x(self) -> None:
        val = get_client()
        self.assertEqual(val, "client")


if __name__ == "__main__":
    unittest.main()
