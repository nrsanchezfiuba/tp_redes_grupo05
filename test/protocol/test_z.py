import unittest


class TestX(unittest.TestCase):
    def test_util_x(self) -> None:
        val = "protocol"
        self.assertEqual(val, "protocol")


if __name__ == "__main__":
    unittest.main()
