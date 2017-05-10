#!/usr/bin/env python


import spynnaker.pyNN as p

from p7_integration_tests.base_test_case import BaseTestCase


def do_run():
    p.setup(timestep=1.0, min_delay=1.0, max_delay=1.0)

    cell_params = {'i_offset':  .1,    'tau_refrac': 3.0, 'v_rest': -65.0,
                   'v_thresh': -51.0,  'tau_syn_E': 2.0,
                   'tau_syn_I': 5.0,   'v_reset': -70.0,
                   'e_rev_E':  0.,     'e_rev_I': -80.}

    # setup test population
    if_pop = p.Population(1, p.IF_cond_exp, cell_params)
    # setup spike sources
    exc_pop = p.Population(1, p.SpikeSourceArray,
                           {'spike_times': [20., 40., 60.]})
    inh_pop = p.Population(1, p.SpikeSourceArray,
                           {'spike_times': [120., 140., 160.]})
    # setup excitatory and inhibitory connections
    listcon = p.FromListConnector([(0, 0, 0.01, 1.0)])
    p.Projection(exc_pop, if_pop, listcon, target='excitatory')
    p.Projection(inh_pop, if_pop, listcon, target='inhibitory')
    # setup recorder
    if_pop.record_v()
    p.run(200.)
    # read out voltage and plot
    V = if_pop.get_v()
    p.end()

    return V


class TestSynapesExcitVsInhib(BaseTestCase):
    def test_run(self):
        do_run()


if __name__ == '__main__':
    V = do_run()
    import pylab  # deferred so unittest are not dependent on it
    pylab.plot(V[:, 1], V[:, 2], '.', label=p.__name__)
    pylab.legend()
    pylab.show()
