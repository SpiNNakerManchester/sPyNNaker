import unittest
import spynnaker.pyNN.utilities.utility_calls as utility_calls
import os, time


class TestUtilityCalls(unittest.TestCase):
    def test_check_directory_exists(self):
        time.sleep(1)
        utility_calls.check_directory_exists_and_create_if_not(os.path.dirname(
            os.path.realpath(__file__)))
        self.assertTrue(os.path.exists(os.path.dirname(
            os.path.realpath(__file__))))

    def test_check_directory_not_exists(self):
        time.sleep(1)
        test_file = os.path.abspath(
            os.path.join(
                os.path.join(__file__,os.pardir),
            "test_utility_call"))
        if os.path.exists(test_file):
            os.rmdir(test_file)
            print "File existed. Deleting..."

        utility_calls.check_directory_exists_and_create_if_not(test_file)

        if os.path.exists(test_file):
            os.rmdir(test_file)
            print "File created successfully. Deleting..."
        else:
            raise AssertionError("File was not created")



    def test_is_conductance(self):
        self.assertEqual(True, False, "NotImplementedError")

    def test_check_weight(self):
        self.assertEqual(True, False, "NotImplementedError")

    def test_check_delay(self):
        self.assertEqual(True, False, "NotImplementedError")

    def test_get_region_base_address_offset(self):
        self.assertEqual(True, False)

    def test_get_ring_buffer_to_input_left_shift(self):
        self.assertEqual(True, False)

    def test_convert_param_to_numpy_random_distribution(self):
        self.assertEqual(True, False)

    def test_convert_param_to_numpy_iterable(self):
        self.assertEqual(True, False)

    def test_convert_param_to_numpy_random(self):
        self.assertEqual(True, False)

    def test_convert_param_to_numpy_exception(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
