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
import numpy


def test_weight_changer_limits():
    sim.setup(timestep=1.0)
    n_neurons = 5
    n_changes = 6
    time_diff = 4
    n_cycles = n_neurons * time_diff

    # Set up so that there is a pre-spike after each change set and that each
    # change happens to each neuron separately
    changes_1 = [[j * n_cycles + i * time_diff + 0
                  for j in range(n_changes)] for i in range(n_neurons)]
    changes_2 = [[j * n_cycles + i * time_diff + 1
                  for j in range(n_changes)] for i in range(n_neurons)]
    pre_times = [[j * n_cycles + i * time_diff + 2
                  for j in range(n_changes)] for i in range(n_neurons)]

    print(changes_1)
    print(changes_2)
    print(pre_times)

    pre = sim.Population(5, sim.SpikeSourceArray(spike_times=pre_times))
    post = sim.Population(5, sim.IF_curr_exp())
    changer_1 = sim.Population(
        5, sim.SpikeSourceArray(spike_times=changes_1))
    changer_2 = sim.Population(
        5, sim.SpikeSourceArray(spike_times=changes_2))

    pre.set_max_atoms_per_core(4)
    post.set_max_atoms_per_core(3)
    changer_1.set_max_atoms_per_core(2)
    changer_2.set_max_atoms_per_core(1)

    changable_proj_1 = sim.Projection(
        pre, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(0.25, 4.5, weight=2.0, delay=1.0))
    changable_proj_2 = sim.Projection(
        pre, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(0.25, 4.5, weight=1.5, delay=1.0))

    change_proj_1 = sim.Projection(
        changer_1, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=0.5, projection=changable_proj_1))
    change_proj_2 = sim.Projection(
        changer_2, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=-0.25, projection=changable_proj_2))

    weights_1 = []
    weights_2 = []

    sim.run(0)

    print(change_proj_1.get('weight', 'list'))
    print(change_proj_2.get('weight', 'list'))

    # Get weights at start
    weights_1.append(
        changable_proj_1.get('weight', 'list', with_address=False))
    weights_2.append(
        changable_proj_2.get('weight', 'list', with_address=False))

    # Do initial run to get past first changes and pre-spike
    sim.run(time_diff - 1)

    # Do the rest of the runs (already done one)
    for i in range((n_neurons * n_changes) - 1):
        weights_1.append(
            changable_proj_1.get('weight', 'list', with_address=False))
        weights_2.append(
            changable_proj_2.get('weight', 'list', with_address=False))

        sim.run(time_diff)

    # Get final weights
    weights_1.append(
        changable_proj_1.get('weight', 'list', with_address=False))
    weights_2.append(
        changable_proj_2.get('weight', 'list', with_address=False))

    sim.end()

    next_weights = [2.0 for _ in range(n_neurons)]
    change = 0
    for w in weights_1:
        assert numpy.array_equal(w, next_weights)
        if next_weights[change] < 4.5:
            next_weights[change] += 0.5
        change = (change + 1) % n_neurons

    next_weights = [1.5 for _ in range(n_neurons)]
    change = 0
    for w in weights_2:
        assert numpy.array_equal(w, next_weights)
        if next_weights[change] > 0.25:
            next_weights[change] -= 0.25
        change = (change + 1) % n_neurons


def test_weight_changer_diffs():
    sim.setup(timestep=1.0)

    # Pre spikes at 5ms intervals
    pre_times = [5, 10, 15]
    # For change 1, do one in segment 1, none in segment 2, two in segment 3
    changes_1 = [1, 12, 13]
    # For change 2, do none in segment 1, two in segment 2, one in segment 3
    changes_2 = [7, 8, 12]

    pre = sim.Population(1, sim.SpikeSourceArray(spike_times=pre_times))
    post = sim.Population(1, sim.IF_curr_exp())
    changer_1 = sim.Population(
        1, sim.SpikeSourceArray(spike_times=changes_1))
    changer_2 = sim.Population(
        1, sim.SpikeSourceArray(spike_times=changes_2))

    changable_proj_1 = sim.Projection(
        pre, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(0, 5, weight=2.5, delay=1.0))
    changable_proj_2 = sim.Projection(
        pre, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChangeable(0, 5, weight=3.0, delay=1.0),
        receptor_type='inhibitory')

    change_proj_1 = sim.Projection(
        changer_1, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=-0.75, projection=changable_proj_1))
    change_proj_2 = sim.Projection(
        changer_2, post, sim.OneToOneConnector(),
        sim.extra_models.WeightChanger(
            weight_change=0.25, projection=changable_proj_2),
        receptor_type='inhibitory')

    weights_1 = []
    weights_2 = []

    sim.run(0)

    print(change_proj_1.get('weight', 'list'))
    print(change_proj_2.get('weight', 'list'))

    # Get weights at start
    weights_1.append(
        changable_proj_1.get('weight', 'list', with_address=False)[0])
    weights_2.append(
        changable_proj_2.get('weight', 'list', with_address=False)[0])

    last_time = 0
    for pre_time in pre_times:
        sim.run((pre_time - last_time) + 1)
        last_time = pre_time + 1

        weights_1.append(
            changable_proj_1.get('weight', 'list', with_address=False)[0])
        weights_2.append(
            changable_proj_2.get('weight', 'list', with_address=False)[0])

    sim.end()

    assert numpy.array_equal(weights_1, [2.5, 1.75, 1.75, 0.25])
    assert numpy.array_equal(weights_2, [3.0, 3.0, 3.50, 3.75])


if __name__ == "__main__":
    test_weight_changer_limits()
