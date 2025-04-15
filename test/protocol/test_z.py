import unittest

from protocol.utils.x import get_protocol


class TestX(unittest.TestCase):
    def test_util_x(self) -> None:
        val = get_protocol()
        self.assertEqual(val, "protocol")


if __name__ == "__main__":
    unittest.main()
