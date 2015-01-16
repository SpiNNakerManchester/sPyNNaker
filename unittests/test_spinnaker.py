import unittest
from spynnaker.pyNN.spinnaker import Spinnaker


class MyTestCase(unittest.TestCase):

    @unittest.skip("Not implemented")
    def test_something(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()
