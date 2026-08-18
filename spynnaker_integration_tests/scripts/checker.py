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

from neo import AnalogSignal, SpikeTrain

from spynnaker.pyNN.models.populations import Population


def check_neuron_data(
        spikes: SpikeTrain, v: AnalogSignal, exc: AnalogSignal,
        expected_spikes: int, simtime: int, label: str, index: int) -> None:

    if len(spikes) != expected_spikes:
        raise AssertionError(
            f"Incorrect number of spikes for neuron {index} in {label}. "
            f"Expected {expected_spikes} found {len(spikes)}")

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
                    f"Incorrect V for neuron {index} at time {t} "
                    f"(which is {t_delta} since last spike) in {label}. "
                    f"Found {v[t].magnitude} but expected 65")
        else:
            target_v = v[t - 1].magnitude + exc[t - 1].magnitude
            if v[t] > target_v:
                raise AssertionError(
                    f"Incorrect V for neuron {index} at time {t} "
                    f"(which is {t_delta} since last spike) in {label}. "
                    f"Found {v[t]} but expected more than {target_v}")
            if v[t] < target_v - 1:
                raise AssertionError(
                    f"Incorrect V for neuron {index} at time {t} "
                    f"(which is {t_delta} since last spike) in {label}. "
                    f"Found {v[t]} but expected more than than {target_v - 1}")


def check_data(pop: Population, expected_spikes: int, simtime: int) -> None:
    neo = pop.get_data("all")
    spikes = neo.segments[0].spiketrains
    v = neo.segments[0].filter(name="v")[0]
    gsyn_exc = neo.segments[0].filter(name="gsyn_exc")[0]
    for i in range(len(spikes)):
        check_neuron_data(spikes[i], v[:, i], gsyn_exc[:, i], expected_spikes,
                          simtime, pop.label, i)
