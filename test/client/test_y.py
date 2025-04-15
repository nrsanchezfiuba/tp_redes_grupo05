import unittest


class TestX(unittest.TestCase):
    def test_util_x(self):
        val = "client"
        self.assertEqual(val, "client")


if __name__ == "__main__":
    unittest.main()
