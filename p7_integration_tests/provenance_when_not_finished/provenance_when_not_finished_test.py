"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
import os
from spinnman.exceptions import SpinnmanTimeoutException
from fake_if_curr import FakeIFCurrExp
from p7_integration_tests.base_test_case import BaseTestCase


class ProvenanceWhenNotFinishedTest(BaseTestCase):
    def test_tun(self):
        with self.assertRaises(SpinnmanTimeoutException):
            p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
            # add to the path the location of the dodgy binary
            # (if_cur_exp with the c_main bodged to result in it
            # running for twice as long as expected)
            p._spinnaker._executable_finder.add_path(os.path.dirname(__file__))
            nNeurons = 200  # number of neurons in each population
            cell_params_lif = {'cm': 0.25,
                               'i_offset': 0.0,
                               'tau_m': 20.0,
                               'tau_refrac': 2.0,
                               'tau_syn_E': 5.0,
                               'tau_syn_I': 5.0,
                               'v_reset': -70.0,
                               'v_rest': -65.0,
                               'v_thresh': -50.0
                               }
            populations = list()
            projections = list()
            weight_to_spike = 2.0
            delay = 17
            loopConnections = list()
            for i in range(0, nNeurons):
                singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike,
                                    delay)
                loopConnections.append(singleConnection)
            injectionConnection = [(0, 0, weight_to_spike, 1)]
            spikeArray = {'spike_times': [[0]]}
            populations.append(p.Population(nNeurons, FakeIFCurrExp,
                                            cell_params_lif, label='pop_1'))
            populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                               label='inputSpikes_1'))
            projections.append(p.Projection(populations[0], populations[0],
                               p.FromListConnector(loopConnections)))
            projections.append(p.Projection(populations[1], populations[0],
                               p.FromListConnector(injectionConnection)))
            populations[0].record_v()
            populations[0].record_gsyn()
            populations[0].record()
            p.run(5000)
            p.end()
