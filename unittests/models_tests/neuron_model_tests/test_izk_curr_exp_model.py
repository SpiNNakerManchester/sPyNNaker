import unittest
from spynnaker.pyNN.models.neuron.builds.izk_curr_exp import IzkCurrExp


class TestIZKCurrExpModel(unittest.TestCase):
    def test_new_izk_curr_exp_model(self):
        n_neurons = 10
        izk_curr_exp = IzkCurrExp(n_neurons, 1000, 1.0)

        self.assertEqual(izk_curr_exp._model_name, "IZK_curr_exp")
        self.assertEqual(len(izk_curr_exp.get_parameters()), 8)
        self.assertEqual(izk_curr_exp._a, 0.02)
        self.assertEqual(izk_curr_exp._b, 0.2)
        self.assertEqual(izk_curr_exp._c, -65.0)
        self.assertEqual(izk_curr_exp._d, 2.0)

        self.assertEqual(izk_curr_exp._i_offset, 0)
        self.assertEqual(izk_curr_exp._tau_syn_E, 5.0)
        self.assertEqual(izk_curr_exp._tau_syn_I, 5.0)


if __name__ == "__main__":
    unittest.main()
