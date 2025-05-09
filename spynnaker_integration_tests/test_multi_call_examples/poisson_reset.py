# Copyright (c) 2023 The University of Manchester
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
from spinn_front_end_common.data.fec_data_view import FecDataView


def test_possion_reset() -> None:
    """ Check that DSG still does the right thing after reset
    """
    sim.setup(1.0)
    sim.set_number_of_synapse_cores(sim.IF_curr_exp, 1)
    noise = sim.Population(100, sim.SpikeSourcePoisson(
        rate=10.0), label="Noise")
    pop = sim.Population(100, sim.IF_curr_exp())
    sim.Projection(noise, pop, sim.OneToOneConnector(), sim.StaticSynapse(1.0))

    sim.run(1000)
    sim.reset()
    # Force a data regeneration here to check Poisson is OK with this
    FecDataView.set_requires_data_generation()
    sim.run(1000)
    sim.end()
