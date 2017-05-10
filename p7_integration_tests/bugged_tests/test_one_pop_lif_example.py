#!/usr/bin/python
import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

    cell_params_lif_in = {'tau_m': 333.33, 'cm': 208.33, 'v_init': 0.0,
                          'v_rest': 0.1, 'v_reset': 0.0, 'v_thresh': 1.0,
                          'tau_syn_E': 1, 'tau_syn_I': 2, 'tau_refrac': 2.5,
                          'i_offset': 3.0}

    pop1 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif_in,
                        label='pop_0')

    pop1.record_v()
    pop1.record_gsyn()
    pop1.record()

    p.run(3000)

    v = pop1.get_v(compatible_output=True)
    gsyn = pop1.get_gsyn(compatible_output=True)
    spikes = pop1.getSpikes(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)


class OnePopLifExample(BaseTestCase):
    def test_run(self):
        nNeurons = 255  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        self.assertLess(9500, len(spikes))
        self.assertGreater(9800, len(spikes))


if __name__ == '__main__':
    nNeurons = 255  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")
