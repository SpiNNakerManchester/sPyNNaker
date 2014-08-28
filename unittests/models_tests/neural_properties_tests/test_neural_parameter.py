import unittest
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class TestingNeuronParameter(unittest.TestCase):
    def test_create_new_neuron_parameter_none_datatype(self):
        np = NeuronParameter(1, None)
        self.assertEqual(np.get_value(), 1)
        self.assertEqual(np.get_dataspec_datatype(), None)


if __name__ == '__main__':
    unittest.main()
