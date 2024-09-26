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


def test_weight_changer():
    sim.setup(timestep=1.0)

    # Set up so that there is a pre-spike after each change and that each
    # change happens to each neuron separately
    pre_times = [[j * 5 + i + 0.25 for j in range(5)] for i in range(1, 6)]
    change_times = [[j * 5 + i for j in range(5)] for i in range(1, 6)]

    print(change_times)

    pre = sim.Population(5, sim.SpikeSourceArray(spike_times=pre_times))
    post_1 = sim.Population(5, sim.IF_curr_exp())
    post_2 = sim.Population(5, sim.IF_curr_exp())
    changer = sim.Population(5, sim.SpikeSourceArray(spike_times=change_times))

    changable_proj_1 = sim.Projection(
        pre, post_1, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(1.0, 3.0, weight=2.0, delay=1.0))
    changable_proj_2 = sim.Projection(
        pre, post_2, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(0.25, 2.0, weight=1.0, delay=1.0))

    change_proj_1 = sim.Projection(
        changer, post_1, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=0.5, projection=changable_proj_1))
    change_proj_2 = sim.Projection(
        changer, post_2, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=-0.25, projection=changable_proj_2))

    weights_1 = []
    weights_2 = []

    sim.run(0.5)

    print(change_proj_1.get('weight', 'list'))
    print(change_proj_2.get('weight', 'list'))

    for i in range(26):
        sim.run(1)

        weights_1.append(changable_proj_1.get('weight', 'list'))
        weights_2.append(changable_proj_2.get('weight', 'list'))

    sim.end()

    for w in weights_1:
        print(w)
    print()
    for w in weights_2:
        print(w)


if __name__ == "__main__":
    test_weight_changer()
