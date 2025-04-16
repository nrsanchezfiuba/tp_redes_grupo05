import unittest


class TestX(unittest.TestCase):
    def test_util_x(self) -> None:
        val = "server"
        self.assertEqual(val, "server")


if __name__ == "__main__":
    unittest.main()
