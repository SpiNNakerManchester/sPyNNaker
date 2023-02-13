# Copyright (c) 2017-2023 The University of Manchester
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

import os
import sys
import numpy
import pyNN.spiNNaker as sim
from spynnaker.pyNN.models.populations import PopulationView
from spinnaker_testbase import BaseTestCase

"""
This is the original way of testing selective recording.

It worked by running the same seeded script twice.
Once recording all and once with selective recording on.

The main selective recording is now done by test_sampling
based on the PatternSpiker.

This is kept mainly for all the useful compare methods.
Which is why most tests are commented out.
"""


def run_script(
        simtime, n_neurons, run_split=1,
        record_spikes=False, spike_rate=None, spike_rec_indexes=None,
        spike_get_indexes=None,
        record_v=False, v_rate=None, v_rec_indexes=None,  v_get_indexes=None,
        record_exc=False, exc_rate=None, exc_rec_indexes=None,
        exc_get_indexes=None,
        record_inh=False, inh_rate=None, inh_rec_indexes=None,
        inh_get_indexes=None,
        file_prefix=""):

    sim.setup(timestep=1)

    pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
    input1 = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                            label="input")
    sim.Projection(input1, pop_1, sim.AllToAllConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    input2 = sim.Population(n_neurons, sim.SpikeSourcePoisson(
        rate=100.0),  label="Stim_Exc", additional_parameters={"seed": 1})
    sim.Projection(input2, pop_1, sim.OneToOneConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    if record_spikes:
        if spike_rec_indexes is None:
            pop_1.record(['spikes'], sampling_interval=spike_rate)
        else:
            view = PopulationView(pop_1, spike_rec_indexes)
            view.record(['spikes'], sampling_interval=spike_rate)
    if record_v:
        if v_rec_indexes is None:
            pop_1.record(['v'], sampling_interval=v_rate)
        else:
            view = PopulationView(pop_1, v_rec_indexes)
            view.record(['v'], sampling_interval=v_rate)
    if record_exc:
        if exc_rec_indexes is None:
            pop_1.record(['gsyn_exc'], sampling_interval=exc_rate)
        else:
            view = PopulationView(pop_1, exc_rec_indexes)
            view.record(['gsyn_exc'], sampling_interval=exc_rate)
    if record_inh:
        if inh_rec_indexes is None:
            pop_1.record(['gsyn_inh'], sampling_interval=inh_rate)
        else:
            view = PopulationView(pop_1, inh_rec_indexes)
            view.record(['gsyn_inh'], sampling_interval=inh_rate)
    for _i in range(run_split):
        sim.run(simtime/run_split)

    if record_spikes:
        if spike_get_indexes is None:
            neo = pop_1.get_data("spikes")
        else:
            view = PopulationView(pop_1, spike_get_indexes)
            neo = view.get_data("spikes")
        spikes = neo.segments[0].spiketrains
        spike_file = file_prefix+"spikes.csv"
        write_spikes(spikes, spike_file)
    else:
        spikes = None

    if record_v:
        if v_get_indexes is None:
            neo = pop_1.get_data("v")
        else:
            view = PopulationView(pop_1, v_get_indexes)
            neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0]
        v_file = file_prefix+"v.csv"
        numpy.savetxt(v_file, v, delimiter=',')
    else:
        v = None

    if record_exc:
        if exc_get_indexes is None:
            neo = pop_1.get_data('gsyn_exc')
        else:
            view = PopulationView(pop_1, exc_get_indexes)
            neo = view.get_data('gsyn_exc')
        exc = neo.segments[0].filter(name='gsyn_exc')[0]
        exc_file = file_prefix+"exc.csv"
        numpy.savetxt(exc_file, exc, delimiter=',')
    else:
        exc = None
    if record_inh:
        if inh_get_indexes is None:
            neo = pop_1.get_data('gsyn_inh')
        else:
            view = PopulationView(pop_1, inh_get_indexes)
            neo = view.get_data('gsyn_inh')
        inh = neo.segments[0].filter(name='gsyn_inh')[0]
        inh_file = file_prefix+"inh.csv"
        numpy.savetxt(inh_file, inh, delimiter=',')
    else:
        inh = None

    sim.end()

    return spikes, v,  exc, inh


def compare_spikearrays(this, full, tolerance=False):
    if numpy.array_equal(this, full):
        return sys.maxsize
    if this[0] != full[0]:
        raise ValueError("Index mismatch")
    if len(this) != len(full):
        print("{} spikes length differ. {} != {}".format(
            this[0], len(this), len(full)))
    i1 = 0
    i2 = 0
    lowest = None
    while i1 < len(this) and i2 < len(full):
        if this[i1] == full[i2]:
            i1 += 1
            i2 += 1
        elif this[i1] < full[i2]:
            print("extra spike {} has spike at {}".format(this[0], this[i1]))
            i1 += 1
            if lowest is None:
                lowest = this[i1]
        elif this[i1] > full[i2]:
            print("spike missing {} no spike at {}".format(this[0], full[i2]))
            i2 += 1
            if lowest is None:
                lowest = full[i2]
    while i1 < len(this):
        print("trailing extra spike {} has spike at {}".format(
            this[0], this[i1]))
        if lowest is None:
            lowest = this[i1]
        i1 += 1
    while i2 < len(full):
        print("trailing spike missing {} no spike at {}".format(
            this[0], full[i2]))
        if lowest is None:
            lowest = full[i2]
        i2 += 1
    if lowest is None:
        lowest = sys.maxsize
    return lowest


def compare_spikes(file_path, full_path, simtime, n_neurons, spike_rate=1,
                   spike_indexes=None, tolerance=sys.maxsize):
    this_spikes = read_spikes(file_path, simtime, n_neurons)
    full_spikes = read_spikes(full_path, simtime, n_neurons, rate=spike_rate,
                              indexes=spike_indexes)
    if len(this_spikes) != len(full_spikes):
        raise ValueError(f"Spikes different length this {len(this_spikes)} "
                         "full {len(full_spikes)}")
    lowest = sys.maxsize
    for this, full in zip(this_spikes, full_spikes):
        low = compare_spikearrays(this, full)
        lowest = min(lowest, low)
    if lowest < tolerance:
        raise ValueError(f"Spikes different from {lowest}")
    print("Spikes equal")
    return lowest


def compare_results(
        simtime, n_neurons,
        record_spikes=False, spike_rate=None, spike_indexes=None,
        record_v=False, v_rate=None, v_indexes=None,
        record_exc=False, exc_rate=None, exc_indexes=None,
        record_inh=False, inh_rate=None, inh_indexes=None, full_prefix="",
        tolerance=sys.maxsize):
    if record_spikes:
        file_path = "spikes.csv"
        full_path = full_prefix+"spikes.csv"
        compare_spikes(file_path, full_path, simtime, n_neurons,
                       spike_rate, spike_indexes, tolerance)
    if record_v:
        file_path = "v.csv"
        full_path = full_prefix+"v.csv"
        compare(file_path, full_path, v_rate, v_indexes)
    if record_exc:
        file_path = "exc.csv"
        full_path = full_prefix+"exc.csv"
        compare(file_path, full_path, exc_rate, exc_indexes)
    if record_inh:
        file_path = "inh.csv"
        full_path = full_prefix+"inh.csv"
        compare(file_path, full_path, inh_rate, inh_indexes)


def merge_indexes(rec_indexes, get_indexes):
    if rec_indexes is None:
        if get_indexes is None:
            return None
        else:
            return get_indexes
    else:
        if get_indexes is None:
            return rec_indexes
        else:
            return [index for index in rec_indexes if index in get_indexes]


def run_and_compare_script(
        simtime, n_neurons, run_split=1,
        record_spikes=False, spike_rate=None, spike_rec_indexes=None,
        spike_get_indexes=None,
        record_v=False, v_rate=None, v_rec_indexes=None, v_get_indexes=None,
        record_exc=False, exc_rate=None, exc_rec_indexes=None,
        exc_get_indexes=None,
        record_inh=False, inh_rate=None, inh_rec_indexes=None,
        inh_get_indexes=None,
        tolerance=sys.maxsize):
    full_prefix = "{}_{}_".format(simtime, n_neurons)
    if (not os.path.exists(full_prefix + "spikes.csv") or
            not os.path.exists(full_prefix + "v.csv") or
            not os.path.exists(full_prefix + "v.csv") or
            not os.path.exists(full_prefix + "v.csv")):
        print("Comparison files do not exist so creating them")
        run_script(
            simtime, n_neurons,
            record_spikes=True,
            record_v=True,
            record_exc=True,
            record_inh=True,
            file_prefix=full_prefix)

    run_script(
        simtime, n_neurons, run_split,
        record_spikes=record_spikes, spike_rate=spike_rate,
        spike_rec_indexes=spike_rec_indexes,
        spike_get_indexes=spike_get_indexes,
        record_v=record_v, v_rate=v_rate, v_get_indexes=v_get_indexes,
        v_rec_indexes=v_rec_indexes,
        record_exc=record_exc, exc_rate=exc_rate,
        exc_get_indexes=exc_get_indexes, exc_rec_indexes=exc_rec_indexes,
        record_inh=record_inh, inh_rate=inh_rate,
        inh_rec_indexes=inh_rec_indexes, inh_get_indexes=inh_get_indexes)

    spike_indexes = merge_indexes(spike_rec_indexes, spike_get_indexes)
    v_indexes = merge_indexes(v_rec_indexes, v_get_indexes)
    exc_indexes = merge_indexes(exc_rec_indexes, exc_get_indexes)
    inh_indexes = merge_indexes(inh_rec_indexes, inh_get_indexes)

    compare_results(
        simtime, n_neurons,
        record_spikes=record_spikes, spike_rate=spike_rate,
        spike_indexes=spike_indexes,
        record_v=record_v, v_rate=v_rate, v_indexes=v_indexes,
        record_exc=record_exc, exc_rate=exc_rate, exc_indexes=exc_indexes,
        record_inh=record_inh, inh_rate=inh_rate, inh_indexes=inh_indexes,
        full_prefix=full_prefix, tolerance=tolerance)


def write_spikes(spikes, spike_file):
    with open(spike_file, "w", encoding="utf-8") as f:
        for spiketrain in spikes:
            f.write("{}".format(spiketrain.annotations["source_index"]))
            for time in spiketrain.times:
                f.write(",{}".format(time.magnitude))
            f.write("\n")


def ordered_rounded_set(in_list, factor, simtime):
    out_list = []
    added = set()
    for s in in_list[1:]:
        raw = float(s)
        if (raw % factor) > 0:
            val = round(raw + factor - (raw % factor), 5)
        else:
            val = raw
        if val < simtime and val not in added:
            out_list.append(val)
            added.add(val)
    out_list.insert(0, in_list[0])
    return out_list


def read_spikes(name, simtime, n_neurons, rate=1, indexes=None):
    spikes = []
    with open(name, encoding="utf-8") as f:
        for line in f:
            parts = line.split(",")
            if len(parts) > 1:
                if indexes is None:
                    if int(parts[0]) < n_neurons:
                        spikes.append(
                            ordered_rounded_set(parts, rate, simtime))
                else:
                    if int(parts[0]) in indexes:
                        spikes.append(
                            ordered_rounded_set(parts, rate, simtime))
    return spikes


def compare(current, full, rate, indexes):
    """ Compares two data files to see if they contain similar data.\
    Ignores data not recorded due to sampling rate or indexes.

    The current data is also read from file so that any float changes \
        due to read write are the same.

    :param current:
    :param full:
    :param rate:
    :param indexes:
    """
    print(current)
    d1 = numpy.loadtxt(current, delimiter=',')
    print(d1.shape)
    if len(d1.shape) == 1:
        d1 = numpy.transpose(numpy.array([d1]))
    print(full)
    d2 = numpy.loadtxt(full, delimiter=',')
    if indexes is None:
        d2_rate = d2[::rate]
    else:
        d2_rate = d2[::rate, indexes]
    print(d2_rate.shape)
    if not numpy.array_equal(d1, d2_rate):
        if d1.shape != d2_rate.shape:
            if d1.shape[0] == 0 or d1.shape[1] == 0:
                return  # Empty so ignore shape
            raise ValueError(
                f"Shape not equal {d1.shape} {d2_rate.shape}")
        for i in range(d1.shape[0]):
            if not numpy.array_equal(d1[i], d2_rate[i]):
                for j in range(len(d1[i])):
                    if d1[i][j] != d2_rate[i][j]:
                        raise ValueError(
                            f"row {i} column{j} index{indexes[j]} "
                            f"current {d1[i][j]} full {d2_rate[i][j]}")


class TestSampling(BaseTestCase):
    """
    def test_big_with_rate(self):
        simtime = 20000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=2,
            record_v=True, v_rate=3,
            record_exc=True, exc_rate=4,
            record_inh=True, inh_rate=5,
            tolerance=simtime-2)

    def test_big_with_rec_index(self):
        simtime = 20000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=1,
            spike_rec_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=1, v_rec_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=1,
            exc_rec_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=1,
            inh_rec_indexes=range(0, n_neurons, 4))

    def test_big_with_get_index(self):
        simtime = 20000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=1,
            spike_get_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=1, v_get_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=1,
            exc_get_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=1,
            inh_get_indexes=range(0, n_neurons, 4))

    def test_big_with_both(self):
        simtime = 20000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=5,
            spike_rec_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=4, v_rec_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=3,
            exc_rec_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=2,
            inh_rec_indexes=range(0, n_neurons, 4))

    def test_medium_split(self):
        simtime = 5000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons, run_split=5,
            record_spikes=True, spike_rate=5,
            spike_rec_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=4, v_rec_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=3,
            exc_rec_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=2,
            inh_rec_indexes=range(0, n_neurons, 4))

    def test_rec_medium(self):
        simtime = 5000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=5,
            spike_rec_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=4, v_rec_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=3,
            exc_rec_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=2,
            inh_rec_indexes=range(0, n_neurons, 4))

    def test_get_medium(self):
        simtime = 5000
        n_neurons = 500
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=5,
            spike_get_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=4, v_get_indexes=range(0, n_neurons, 2),
            record_exc=True, exc_rate=3,
            exc_get_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=2,
            inh_get_indexes=range(0, n_neurons, 4))
    """

    def test_mixed_medium(self):
        simtime = 500
        n_neurons = 300
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=5,
            spike_get_indexes=range(0, n_neurons, 2),
            record_v=True, v_rate=4, v_rec_indexes=range(0, n_neurons, 2),
            v_get_indexes=range(0, n_neurons, 4),
            record_exc=True, exc_rate=3,
            exc_rec_indexes=range(0, n_neurons, 2),
            exc_get_indexes=range(0, n_neurons, 3),
            record_inh=True, inh_rate=2,
            inh_rec_indexes=range(0, n_neurons, 4),
            inh_get_indexes=range(2, n_neurons, 4))

    """
    def test_one(self):
        simtime = 500
        n_neurons = 300
        run_and_compare_script(
            simtime, n_neurons,
            record_spikes=True, spike_rate=5,
            spike_rec_indexes=[0],
            record_v=True, v_rec_indexes=[0],
            record_exc=True, exc_rec_indexes=[0],
            record_inh=True, inh_rec_indexes=[0])
    """


if __name__ == '__main__':
    _simtime = 20000
    _n_neurons = 500

    run_and_compare_script(
        _simtime, _n_neurons,
        record_spikes=True, spike_rate=2, spike_indexes=None,
        record_v=True, v_rate=3, v_indexes=None,
        record_exc=True, exc_rate=4, exc_indexes=None,
        record_inh=True, inh_rate=5, inh_indexes=None)
