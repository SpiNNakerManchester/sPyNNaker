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

from typing import Optional, Tuple, Union

import numpy
from pyNN.space import BaseStructure
import pyNN.spiNNaker as sim

from spinnaker_testbase import BaseTestCase

from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.projection import Projection

SOURCES = 5
DESTINATIONS = 10


class TestFixedNumberPreConnector(BaseTestCase):

    def check_weights(
            self, projection: Projection, connections: int,
            with_replacement: bool, allow_self_connections: bool) -> None:
        weights = projection.get(["weight"], "list")
        print(weights)
        last_source = -1
        last_destination = -1
        for (source, destination, _) in weights:
            if source != last_source:
                last_source = source
            else:
                if not with_replacement:
                    self.assertNotEqual(last_destination, destination)
            last_destination = destination
            if not allow_self_connections:
                self.assertNotEqual(source, destination)

    def check_self_connect(self, connections: int, with_replacement: bool,
                           allow_self_connections: bool) -> None:
        sim.setup(1.0)
        pop = sim.Population(DESTINATIONS, sim.IF_curr_exp(), label="pop")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop, pop, sim.FixedNumberPreConnector(
                connections, with_replacement=with_replacement,
                allow_self_connections=allow_self_connections),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, connections, with_replacement,
                           allow_self_connections)
        sim.end()

    def check_other_connect(
            self, connections: int, with_replacement: bool) -> None:
        sim.setup(1.0)
        pop1 = sim.Population(SOURCES, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(DESTINATIONS, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPreConnector(
                connections, with_replacement=with_replacement),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, connections, with_replacement,
                           allow_self_connections=True)
        sim.end()

    def test_replace_self(self) -> None:
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_replace_no_self(self) -> None:
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_no_replace_self(self) -> None:
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_no_replace_no_self(self) -> None:
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            SOURCES-2, with_replacement, allow_self_connections)

    def test_with_many_replace_self(self) -> None:
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS+2, with_replacement, allow_self_connections)

    def test_all_no_replace_self(self) -> None:
        with_replacement = False
        allow_self_connections = True
        self.check_self_connect(
            SOURCES, with_replacement, allow_self_connections)

    def test_all_no_replace_no_self(self) -> None:
        with_replacement = False
        allow_self_connections = False
        with self.assertRaises(SpynnakerException):
            self.check_self_connect(
                DESTINATIONS, with_replacement, allow_self_connections)
        # We have to end here as the exception happens before end
        sim.end()

    def test_all_replace_no_self(self) -> None:
        with_replacement = False
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS, with_replacement, allow_self_connections)

    def test_replace_other(self) -> None:
        with_replacement = True
        self.check_other_connect(SOURCES-2, with_replacement)

    def test_no_replace_other(self) -> None:
        with_replacement = False
        self.check_other_connect(SOURCES-2, with_replacement)

    def test_replace_other_many(self) -> None:
        with_replacement = True
        self.check_other_connect(SOURCES+3, with_replacement)

    def test_no_replace_other_too_many(self) -> None:
        with_replacement = False
        with self.assertRaises(SpynnakerException):
            self.check_other_connect(SOURCES+3, with_replacement)
        # We have to end here as the exception happens before end
        sim.end()

    def test_get_before_run(self) -> None:
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPreConnector(2),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        self.assertEqual(6, len(weights))
        sim.end()

    def test_with_delays(self) -> None:
        sim.setup(1.0)
        # Break up the pre population as that is where delays happen
        sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, 50)
        pop1 = sim.Population(100, sim.SpikeSourceArray([1]), label="pop1")
        pop2 = sim.Population(10, sim.IF_curr_exp(), label="pop2")
        pop2.record("spikes")
        # Choose to use delay extensions
        synapse_type = sim.StaticSynapse(weight=0.5, delay=17)
        conn = sim.FixedNumberPreConnector(10)
        projection = sim.Projection(
            pop1, pop2, conn, synapse_type=synapse_type)
        delays = projection.get(["delay"], "list")
        sim.run(30)
        # There are 100 connections, as there are 10 for each post-neuron
        assert len(delays) == 100
        # If the delays are done right, all pre-spikes should arrive at the
        # same time causing each neuron in the post-population to spike
        spikes = pop2.get_data("spikes").segments[0].spiketrains
        for s in spikes:
            assert len(s) == 1
        sim.end()

    def do_fixed_number_nd_run(
            self, neurons_per_core_pre: Union[int, Tuple[int, ...]],
            pre_size: int, pre_shape: Optional[BaseStructure],
            neurons_per_core_post: int, post_size: int, post_shape: None,
            fixed_n: int) -> None:
        sim.setup(1.0)
        pre = sim.Population(
            pre_size, sim.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = sim.Population(
            post_size, sim.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)
        proj = sim.Projection(
            pre, post, sim.FixedNumberPreConnector(fixed_n),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        sim.end()

        assert all(numpy.bincount(conns[:, 1]) == fixed_n)

    def do_fixed_number_nd_run_no_self(
            self, neurons_per_core: Tuple[int, ...], size: int,
            shape: BaseStructure, fixed_n: int) -> None:
        sim.setup(1.0)
        pop = sim.Population(
            size, sim.IF_curr_exp(), structure=shape)
        pop.set_max_atoms_per_core(neurons_per_core)
        proj = sim.Projection(
            pop, pop, sim.FixedNumberPreConnector(
                fixed_n, allow_self_connections=False),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        sim.end()

        assert all(numpy.bincount(conns[:, 1]) == fixed_n)
        assert all(i != j for i, j in conns)

    def test_fixed_number_1d(self) -> None:
        self.do_fixed_number_nd_run(7, 100, None, 8, 50, None, 10)

    def test_fixed_number_3d_to_1d(self) -> None:
        self.do_fixed_number_nd_run(
            (3, 4, 2), 3 * 8 * 8, sim.Grid3D(3 / 8, 3 / 8),
            11, 30, None, 11)

    def test_fixed_number_2d_no_self(self) -> None:
        self.do_fixed_number_nd_run_no_self(
            (5, 3), 10 * 15, sim.Grid2D(10 / 15), 50)
