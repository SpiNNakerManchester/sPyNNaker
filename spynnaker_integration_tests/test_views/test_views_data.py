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

import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities import neo_convertor


class TestViews(BaseTestCase):

    def set_with_views(self):
        sim.setup(timestep=1.0)

        # create two pops that behave identical
        pop_1 = sim.Population(10, sim.IF_curr_exp(), label="pop_1")
        pop_2 = sim.Population(10, sim.IF_curr_exp(), label="pop_1")
        input = sim.Population(10, sim.SpikeSourceArray(
            spike_times=[[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]),
            label="input")
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.Projection(
            input, pop_2, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=1))

        # record all on pop 1
        pop_1.record(["spikes", "v"])
        # part record on pop 2
        pop_2[2:5].record("spikes")
        pop_2[4, 8].record("spikes")
        pop_2[1:7].record("v")

        simtime = 30
        sim.run(simtime)

        # get all data
        neo1 = pop_1.get_data(variables=["spikes", "v"])
        v1neo = neo1.segments[0].filter(name='v')[0]
        v1convert = neo_convertor.convert_analog_signal(v1neo)
        v1matrix = pop_1.spinnaker_get_data("v", as_matrix=True)
        v1tuple = pop_1.spinnaker_get_data("v")
        spikes1neo = neo1.segments[0].spiketrains
        spikes1convert = neo_convertor.convert_spikes(neo1)
        spikes1tuple = pop_1.spinnaker_get_data("spikes")

        # get everything recorded on pop2
        neo2all = pop_2.get_data(variables=["spikes", "v"])
        v2allneo = neo2all.segments[0].filter(name='v')[0]
        v2allconvert = neo_convertor.convert_analog_signal(v2allneo)
        spikes2allneo = neo2all.segments[0].spiketrains
        spikes2alltuple = pop_2.spinnaker_get_data("spikes")
        v2allmatrix = pop_2.spinnaker_get_data("v", as_matrix=True)
        v2alltuple = pop_2.spinnaker_get_data("v")

        # get using same ids all record
        spikes2viewtuple = pop_2[2, 3, 4, 8].spinnaker_get_data("spikes")
        v2viewmatrix = pop_2[1:7].spinnaker_get_data("v", as_matrix=True)
        v2viewtuple = pop_2[1:7].spinnaker_get_data("v")

        # get view different to recorded
        neo2part = pop_2[0:5].get_data(variables=["spikes", "v"])
        v2partneo = neo2part.segments[0].filter(name='v')[0]
        v2partconvert = neo_convertor.convert_analog_signal(v2partneo)
        spikes2partneo = neo2part.segments[0].spiketrains
        spikes2parttuple = pop_2[0:5].spinnaker_get_data("spikes")
        v2partmatrix = pop_2[0:5].spinnaker_get_data("v", as_matrix=True)
        v2parttuple = pop_2[0:5].spinnaker_get_data("v")

        sim.end()

        # check all
        s1e = [[0, 7.], [1, 8.], [2, 9.], [3, 10.], [4, 11.], [5, 12.],
               [6, 13.], [7, 14.], [8, 15.], [9, 16.]]
        assert (numpy.array_equal(spikes1tuple, s1e))
        assert (numpy.array_equal(spikes1convert, s1e))
        assert (numpy.array_equal(v1convert, v1tuple))
        for id, time, val in v1tuple:
            assert (v1matrix[int(time)][int(id)] == val)

        # check pop2 all recorded
        for id in [2, 3, 4, 8]:
            assert (spikes1neo[id] == spikes2allneo[id])
        for id in [0, 1, 5, 6, 7, 9]:
            assert (len(spikes2allneo[id]) == 0)
        s2e = [[2, 9.], [3, 10.], [4, 11.], [8, 15]]
        assert (numpy.array_equal(spikes2alltuple, s2e))
        assert (numpy.array_equal(spikes2viewtuple, s2e))

        assert (v2allneo.shape == (30, 6))
        for i, id in enumerate(range(1, 7)):
            a = v1neo[:, id]
            b = v2allneo[:, i]
            c = v2allmatrix[:, i]
            d = v2viewmatrix[:, i]
            assert (len(a) == len(b))
            for j in range(len(a)):
                assert (a[j] == b[j] == c[j] == d[j])

        assert (numpy.array_equal(v2allconvert, v2alltuple))
        assert (numpy.array_equal(v2allconvert, v2viewtuple))

        # check pop2 part recorded
        for id in [2, 3, 4]:
            assert (spikes1neo[id] == spikes2partneo[id])
        for id in [0, 1]:
            assert (len(spikes2partneo[id]) == 0)
        s2ea = [[2, 9.], [3, 10.], [4, 11.]]
        assert (numpy.array_equal(spikes2parttuple, s2ea))

        assert (v2partneo.shape == (30, 4))
        for i, id in enumerate(range(1, 5)):
            a = v1neo[:, id]
            b = v2partneo[:, i]
            c = v2partmatrix[:, i]
            for j in range(len(a)):
                assert (a[j] == b[j] == c[j])
        for id, time, val in v2parttuple:
            assert (v1matrix[int(time)][int(id)] == val)
        assert (numpy.array_equal(v2partconvert, v2parttuple))

    def test_set_with_views(self):
        self.runsafe(self.set_with_views)
