import unittest
from spynnaker.pyNN.models.neuron.builds.if_cond_exp import IFCondExp


class TestIFCondExpModel(unittest.TestCase):
    def test_new_if_cond_exp_model(self):
        cell_params_lif = {'cm': 0.25,
                           'i_offset': 0.0,
                           'tau_m': 20.0,
                           'tau_refrac': 0.1,
                           'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0,
                           'v_reset': -65.0,
                           'v_rest': -65.0,
                           'v_thresh': -50.0,
                           'e_rev_E': 0.0,
                           'e_rev_I': -70.0}
        cell_params_lif = {
            'tau_m': 20,
            'cm': 1.0,
            'e_rev_E': 0.0,
            'e_rev_I': -70.0,
            'v_rest': -65.0,
            'v_reset': -65.0,
            'v_thresh': -50.0,
            'tau_syn_E': 5.0,
            'tau_syn_I': 5.0,
            'tau_refrac': 0.1,
            'i_offset': 0}
        n_neurons = 10
        if_cond_exp = IFCondExp(n_neurons, 1000, 1.0)
        self.assertEqual(if_cond_exp.model_name(), "IF_cond_exp")
        self.assertEqual(len(if_cond_exp.get_parameters()), 12)
        self.assertEqual(if_cond_exp._v_thresh, cell_params_lif['v_thresh'])
        self.assertEqual(if_cond_exp._v_reset, [cell_params_lif['v_reset']])
        self.assertEqual(if_cond_exp._v_rest, cell_params_lif['v_rest'])
        self.assertEqual(if_cond_exp._tau_m, cell_params_lif['tau_m'])
        self.assertEqual(if_cond_exp._tau_refrac,
                         [cell_params_lif['tau_refrac']])

        self.assertEqual(if_cond_exp._tau_syn_I, cell_params_lif['tau_syn_I'])
        self.assertEqual(if_cond_exp._tau_syn_E, cell_params_lif['tau_syn_E'])
        self.assertEqual(if_cond_exp._i_offset, cell_params_lif['i_offset'])
        self.assertEqual(if_cond_exp._cm, cell_params_lif['cm'])

        self.assertEqual(if_cond_exp._e_rev_E, cell_params_lif['e_rev_E'])
        self.assertEqual(if_cond_exp._e_rev_I, cell_params_lif['e_rev_I'])


if __name__ == "__main__":
    unittest.main()