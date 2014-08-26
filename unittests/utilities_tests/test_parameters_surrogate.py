import unittest
from spynnaker.pyNN.utilities.parameters_surrogate \
    import PyNNParametersSurrogate


class MyTestVertex(object):
    def __init__(self):
        self.cm = 0.2
        self.tau_refract = 0.0
        self.tau_syn_E = 5.0
        self.n_atoms = 5


class TestParametersSurrogate(unittest.TestCase):
    def test_surrogate_get_item(self):
        test_vertex = MyTestVertex()
        self.assertEqual(test_vertex.cm, 0.2)
        self.assertEqual(test_vertex.tau_refract, 0.0)
        self.assertEqual(test_vertex.tau_syn_E, 5.0)
        surrogate = PyNNParametersSurrogate(test_vertex)
        self.assertEqual(surrogate['cm'], 0.2)
        self.assertEqual(surrogate['tau_refract'], 0.0)
        self.assertEqual(surrogate['tau_syn_E'], 5.0)

    def test_surrogate_set_item(self):
        test_vertex = MyTestVertex()
        self.assertEqual(test_vertex.cm, 0.2)
        self.assertEqual(test_vertex.tau_refract, 0.0)
        self.assertEqual(test_vertex.tau_syn_E, 5.0)
        surrogate = PyNNParametersSurrogate(test_vertex)
        surrogate['cm'] = 2.0
        surrogate['tau_refract'] = 10.5
        surrogate['tau_syn_E'] = 15
        self.assertEqual(surrogate['cm'], 2.0)
        self.assertEqual(surrogate['tau_refract'], 10.5)
        self.assertEqual(surrogate['tau_syn_E'], 15)
        self.assertEqual(test_vertex.cm, 2.0)
        self.assertEqual(test_vertex.tau_refract, 10.5)
        self.assertEqual(test_vertex.tau_syn_E, 15)


    def test_surrogate_get_item_exception(self):
        test_vertex = MyTestVertex()
        surrogate = PyNNParametersSurrogate(test_vertex)
        with self.assertRaises(Exception):
            print surrogate['tau_rev_e']


    def test_surrogate_set_item_exception(self):
        test_vertex = MyTestVertex()
        surrogate = PyNNParametersSurrogate(test_vertex)
        with self.assertRaises(Exception):
            surrogate['tau_rev_e'] = 5


if __name__ == '__main__':
    unittest.main()
