# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)


def stdp_with_self_connection():

    sim.setup(timestep=1.0)

    input_pop1 = sim.Population(64, sim.SpikeSourcePoisson(rate=10),
                                label='input1')
    main_pop = sim.Population(
        64, sim.IF_curr_exp, label='main',
        additional_parameters={
            'splitter': SplitterAbstractPopulationVertexNeuronsSynapses(1)})

    delay1 = sim.RandomDistribution('uniform', (2, 3))
    delayself = sim.RandomDistribution('uniform', (5, 6))

    stdpmodel = sim.STDPMechanism(
        timing_dependence=sim.SpikePairRule(),
        weight_dependence=sim.AdditiveWeightDependence(),
        weight=0.3, delay=delay1)

    sim.Projection(
        input_pop1, main_pop, sim.AllToAllConnector(), synapse_type=stdpmodel,
        receptor_type='excitatory')

    sim.Projection(
        main_pop, main_pop, sim.AllToAllConnector(),
        synapse_type=sim.StaticSynapse(weight=0.2, delay=delayself),
        receptor_type='inhibitory')

    sim.run(1000)

    sim.end()


class TestSTDPWithSelfConnection(BaseTestCase):

    def test_stdp_with_self_connection(self):
        self.runsafe(stdp_with_self_connection)


if __name__ == '__main__':
    stdp_with_self_connection()
