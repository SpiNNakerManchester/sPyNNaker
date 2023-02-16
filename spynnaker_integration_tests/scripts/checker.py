# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def check_neuron_data(spikes, v, exc, expected_spikes, simtime, label, index):

    if len(spikes) != expected_spikes:
        raise AssertionError(
            "Incorrect number of spikes for neuron {} in {}. "
            "Expected {} found {}".
            format(index, label, expected_spikes, len(spikes)))

    # Add a tolerance for when offset goes too early or a bit late
    last_spike = spikes[0].magnitude - 8
    iter_spikes = iter(spikes)
    next_spike = int(next(iter_spikes).magnitude)
    for t in range(simtime):
        if t > next_spike:
            last_spike = next_spike
            try:
                next_spike = int(next(iter_spikes).magnitude)
            except StopIteration:
                next_spike = simtime
        t_delta = t - last_spike
        if t_delta <= 2:
            if v[t].magnitude != -65:
                raise AssertionError(
                    "Incorrect V for neuron {} at time {} "
                    "(which is {} since last spike) in {}. "
                    "Found {} but expected 65".format(
                        index, t, t_delta, label, v[t].magnitude))
        else:
            target_v = v[t - 1].magnitude + exc[t - 1].magnitude
            if v[t] > target_v:
                raise AssertionError(
                    "Incorrect V for neuron {} at time {} "
                    "(which is {} since last spike) in {}. "
                    "Found {} but expected more than {}".format(
                        index, t, t_delta, label, v[t], target_v))
            if v[t] < target_v - 1:
                raise AssertionError(
                    "Incorrect V for neuron {} at time {} "
                    "(which is {} since last spike) in {}. "
                    "Found {} but expected more than than {}".format(
                        index, t, t_delta, label, v[t], target_v - 1))


def check_data(pop, expected_spikes, simtime):
    neo = pop.get_data("all")
    spikes = neo.segments[0].spiketrains
    v = neo.segments[0].filter(name="v")[0]
    gsyn_exc = neo.segments[0].filter(name="gsyn_exc")[0]
    for i in range(len(spikes)):
        check_neuron_data(spikes[i], v[:, i], gsyn_exc[:, i], expected_spikes,
                          simtime, pop.label, i)
