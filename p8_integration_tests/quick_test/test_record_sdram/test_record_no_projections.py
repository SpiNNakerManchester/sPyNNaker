import spynnaker8 as sim
from p8_integration_tests.base_test_case import BaseTestCase


class SynfireProjectionOnSameChip(BaseTestCase):

    def test_no_projections(self):
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        pop_1.record(["spikes", "v"])
        sim.run(10)
