# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
