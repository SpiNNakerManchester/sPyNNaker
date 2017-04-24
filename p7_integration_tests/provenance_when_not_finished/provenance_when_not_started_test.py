import spynnaker.pyNN as p
from testfixtures import LogCapture
from p7_integration_tests.base_test_case import BaseTestCase


def do_run():
    # this test ensures there is too much dtcm used up, thus crashes during
    # initisation
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

    input = p.Population(1024, p.SpikeSourcePoisson, {'rate': 10}, "input")
    relay_on = p.Population(1024, p.IF_curr_exp, {}, "input")

    t_rule_LGN = p.SpikePairRule(tau_plus=17, tau_minus=34)
    w_rule_LGN = p.AdditiveWeightDependence(w_min=0.0, w_max=0.3, A_plus=0.01,
                                            A_minus=0.0085)
    stdp_model_LGN = p.STDPMechanism(timing_dependence=t_rule_LGN,
                                     weight_dependence=w_rule_LGN)
    s_d_LGN = p.SynapseDynamics(slow=stdp_model_LGN)
    p.Projection(input, relay_on, p.OneToOneConnector(weights=1),
                 synapse_dynamics=s_d_LGN, target='excitatory')

    p.run(1000)
    p.end()


class ProvenanceWhenNotStartedTest(BaseTestCase):
    def test_error(self):
        with LogCapture() as l:
            try:
                do_run()
                self.assertTrue(False)
            except:
                self.assert_logs_error(l.records, "Out of DTCM")


if __name__ == '__main__':
    do_run()
