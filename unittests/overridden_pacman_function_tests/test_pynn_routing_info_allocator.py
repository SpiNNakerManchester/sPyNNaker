import unittest
from spynnaker.pyNN.overridden_pacman_functions.pynn_routing_info_allocator \
    import PyNNRoutingInfoAllocator


class MyTestCase(unittest.TestCase):

    @unittest.skip("Not implemented")
    def test_something(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()
