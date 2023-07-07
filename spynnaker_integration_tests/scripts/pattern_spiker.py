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
import numpy
import math
from spynnaker.pyNN.models.populations import PopulationView


class PatternSpiker(object):
    V_PATTERN = [-65.0, -64.024658203125, -63.09686279296875,
                 -62.214324951171875,
                 -61.37481689453125, -60.576263427734375, -59.816650390625,
                 -59.09405517578125, -58.406707763671875, -57.752899169921875,
                 -57.130950927734375, -56.539337158203125, -55.976593017578125,
                 -55.4412841796875, -54.93206787109375, -54.44769287109375,
                 -53.9869384765625, -53.54864501953125, -53.131744384765625,
                 -52.73516845703125, -52.357940673828125, -51.999114990234375,
                 -51.65777587890625, -51.33306884765625, -51.024200439453125,
                 -50.73040771484375, -50.450927734375, -50.185089111328125]
    V_COUNT = len(V_PATTERN)

    def create_population(self, sim, n_neurons, label,
                          spike_rate=None, spike_rec_indexes=None,
                          v_rate=None, v_rec_indexes=None):

        v_start = self.V_PATTERN * int(math.ceil(n_neurons/self.V_COUNT))
        v_start = v_start[:n_neurons]
        pop = sim.Population(n_neurons,
                             sim.IF_curr_exp(i_offset=1, tau_refrac=0),
                             label=label)
        pop.initialize(v=v_start)
        if spike_rec_indexes is None:
            pop.record(['spikes'], sampling_interval=spike_rate)
        else:
            view = PopulationView(pop, spike_rec_indexes)
            view.record(['spikes'], sampling_interval=spike_rate)
        if v_rec_indexes is None:
            pop.record(['v'], sampling_interval=v_rate)
        else:
            view = PopulationView(pop, v_rec_indexes)
            view.record(['v'], sampling_interval=v_rate)
        return pop

    def check_v(self, v, label, v_rate, v_rec_indexes, is_view, missing):
        if v_rate is None:
            v_rate = 1
        if v_rec_indexes is None:
            v_rec_indexes = range(len(v[0]))
        else:
            actual_indexes = list(v.annotations["channel_names"])

            if missing:
                v_rec_indexes = [index for index in v_rec_indexes
                                 if index in actual_indexes]
            if actual_indexes != v_rec_indexes:
                if is_view:
                    raise AssertionError(
                        "Unexpected neuron order for V in {}. "
                        "Found {} but expected {}".format(
                            label, actual_indexes, v_rec_indexes))
                for neuron in v_rec_indexes:
                    if neuron not in actual_indexes:
                        raise AssertionError(
                            "Missing V for {}. No Data for {}".format(
                                label, neuron))
                v_rec_indexes = actual_indexes
        for i, neuron in enumerate(v_rec_indexes):
            for t in range(len(v)):
                if v[t, i] != self.V_PATTERN[
                        (t * v_rate + neuron) % self.V_COUNT]:
                    raise AssertionError(
                        "Incorrect V for neuron {} at time {} in {}. "
                        "Found {} but expected {}".format(
                            neuron, t, label, v[t, i],
                            self.V_PATTERN[(t + neuron) % self.V_COUNT]))

    def check_spikes(
            self, spikes, simtime, label, spike_rate, spike_rec_indexes):
        for neuron in range(len(spikes)):
            if spike_rec_indexes and neuron not in spike_rec_indexes:
                continue
            first = (self.V_COUNT - neuron - 1) % self.V_COUNT
            expected_spikes = list(range(first, simtime, self.V_COUNT))
            if spike_rate:
                adjusted_spikes = [math.ceil(i/spike_rate) * spike_rate
                                   for i in expected_spikes]
                adjusted_spikes = [i for i in adjusted_spikes if i < simtime]
            else:
                adjusted_spikes = expected_spikes
            current = spikes[neuron].magnitude
            if not numpy.array_equal(current, adjusted_spikes):
                if spike_rate:
                    raise AssertionError(
                        "Incorrect spikes for neuron {} in {}. "
                        "Found {} but expected {} adjusted from {}".format(
                            neuron, label, spikes[neuron], adjusted_spikes,
                            expected_spikes))
                else:
                    raise AssertionError(
                        "Incorrect spikes for neuron {} in {}. "
                        "Found {} but expected {}".format(
                            neuron, label, spikes[neuron], adjusted_spikes, ))

    def check(self, pop, simtime, spike_rate=None, spike_rec_indexes=None,
              v_rate=None, v_rec_indexes=None, is_view=False, missing=False):
        if is_view:
            neo = pop.get_data("spikes")
            spikes = neo.segments[0].spiketrains
            neo = pop[v_rec_indexes].get_data("v")
            v = neo.segments[0].filter(name="v")[0]
        else:
            neo = pop.get_data("all")
            spikes = neo.segments[0].spiketrains
            v = neo.segments[0].filter(name="v")[0]
        self.check_spikes(
            spikes, simtime, pop.label, spike_rate, spike_rec_indexes)
        self.check_v(v, pop.label, v_rate, v_rec_indexes, is_view, missing)


if __name__ == '__main__':
    """
    Main method for algorithm checking
    """
    import pyNN.spiNNaker as sim
    ps = PatternSpiker()
    sim.setup(timestep=1)
    simtime = 100
    spike_rate = 5
    spike_rec_indexes = [1, 13, 5, 7, 5, 9, 10]
    v_rec_indexes = [0, 45, 21, 32, 45]
    v_rate = 3
    pop = ps.create_population(sim, 100, "test", spike_rate=spike_rate,
                               spike_rec_indexes=spike_rec_indexes,
                               v_rate=v_rate, v_rec_indexes=v_rec_indexes)
    sim.run(simtime)
    ps.check(pop, simtime,
             spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
             v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)
    sim.end()
