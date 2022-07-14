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

import numpy
import pyNN.spiNNaker as sim
from spynnaker.pyNN.exceptions import SpynnakerException
from spinnaker_testbase import BaseTestCase
from pyNN.random import NumpyRNG

SOURCES = 5
DESTINATIONS = 10
OVERFLOW = 6


class ConnectorsTest(BaseTestCase):

    def test_onetoone_multicore_population_views(self):
        self.runsafe(self.onetoone_multicore_population_views)

    def spike_received_count(self, v_line):
        counts = []
        for v in v_line:
            if v < -64:
                counts.append(0)
            elif v < -62.5:  # -63.0
                counts.append(1)
            elif v < -60.5:  # -61.0
                counts.append(2)
            elif v < -58:  # 59.0
                counts.append(3)
            elif v < -56:  # -57.0
                counts.append(4)
            elif v < -54:  # --55.0
                counts.append(5)
            else:
                counts.append(OVERFLOW)
        return counts

    def calc_spikes_received(self, v):
        counts = list()
        counts.append(self.spike_received_count(v[2]))
        counts.append(self.spike_received_count(v[22]))
        counts.append(self.spike_received_count(v[42]))
        counts.append(self.spike_received_count(v[62]))
        counts.append(self.spike_received_count(v[82]))
        return counts

    def check_counts(self, counts, connections, repeats):
        count = None
        for count in counts:
            if not repeats:
                self.assertEqual(1, max(count))
        if max(count) < OVERFLOW:
            self.assertEqual(connections, sum(count))

    def check_connection(self, projection, destination, connections, repeats,
                         conn_type, n_destinations=DESTINATIONS):
        neo = destination.get_data(["v"])
        v = neo.segments[0].filter(name="v")[0]
        weights = projection.get(["weight"], "list")
        counts = self.calc_spikes_received(v)

        expected = numpy.zeros([SOURCES, n_destinations])
        for weight in weights:
            src = weight[0]
            dest = weight[1]
            expected[src][dest] += 1
        the_max = max(map(max, counts))
        if not numpy.array_equal(expected, counts):
            if the_max < OVERFLOW:
                print(counts)
                print(expected)
                raise AssertionError("Weights and v differ")

        for (source, destination, _) in weights:
            self.assertLess(source, SOURCES)
            self.assertLess(destination, n_destinations)
        if conn_type == "post":
            self.assertEqual(connections * SOURCES, len(weights))
            self.check_counts(counts, connections, repeats)
        elif conn_type == "pre":
            self.assertEqual(connections * n_destinations, len(weights))
            self.check_counts(numpy.transpose(counts), connections, repeats)
        elif conn_type == "one":
            self.assertEqual(connections, len(weights))
            last_source = -1
            for (source, destination, _) in weights:
                self.assertNotEqual(source, last_source)
                last_source = source
                self.assertEqual(source, destination)
            while len(counts) > n_destinations:
                no_connections = counts.pop()
                self.assertEqual(0, sum(no_connections))
            self.check_counts(counts, 1, repeats)
        else:
            self.assertEqual(connections, len(weights))
            if not repeats:
                self.assertEqual(1, the_max)
            if the_max < OVERFLOW:
                self.assertEqual(connections, sum(map(sum, counts)))

    def check_connector(self, connector, connections, repeats,
                        conn_type="post", n_destinations=DESTINATIONS):
        sim.setup(1.0)
        # sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)

        in_pop = sim.Population(SOURCES, sim.SpikeSourceArray(
            spike_times=[[0], [20], [40], [60], [80]]), label="in_pop")
        destination = sim.Population(
            n_destinations, sim.IF_curr_exp(
                tau_syn_E=1, tau_refrac=0,  tau_m=1), label="destination")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            in_pop, destination, connector, synapse_type=synapse_type)
        destination.record("v")
        sim.run(100)
        self.check_connection(
            projection, destination, connections, repeats, conn_type,
            n_destinations)
        sim.end()

    def one_to_one(self):
        connections = min(SOURCES, DESTINATIONS)
        with_replacement = False
        self.check_connector(
            sim.OneToOneConnector(), connections,  with_replacement,
            conn_type="one")

    def test_one_to_one(self):
        self.runsafe(self.one_to_one)

    def one_to_one_short_destination(self):
        n_destinations = SOURCES-1
        connections = min(SOURCES, n_destinations)
        with_replacement = False
        self.check_connector(
            sim.OneToOneConnector(), connections, with_replacement,
            conn_type="one", n_destinations=4)

    def test_one_to_one_short_destination(self):
        self.runsafe(self.one_to_one_short_destination)

    def total_connector_with_replacement(self):
        connections = 20
        with_replacement = True
        self.check_connector(
            sim.FixedTotalNumberConnector(
                connections, with_replacement=with_replacement),
            connections,  with_replacement, conn_type="total")

    def test_total_connector_with_replacement(self):
        self.runsafe(self.total_connector_with_replacement)

    def total_connector_no_replacement(self):
        connections = 20
        with_replacement = False
        self.check_connector(
            sim.FixedTotalNumberConnector(
                connections, with_replacement=with_replacement),
            connections,  with_replacement, conn_type="total")

    def test_total_connector_no_replacement(self):
        self.runsafe(self.total_connector_no_replacement)

    def total_connector_with_replacement_many(self):
        connections = 60
        with_replacement = True
        self.check_connector(
            sim.FixedTotalNumberConnector(
                connections, with_replacement=with_replacement),
            connections,  with_replacement, conn_type="total")

    def test_total_connector_with_replacement_many(self):
        self.runsafe(self.total_connector_with_replacement_many)

    def total_connector_too_many(self):
        connections = 60
        with_replacement = False
        with self.assertRaises(SpynnakerException):
            self.check_connector(
                sim.FixedTotalNumberConnector(
                    connections, with_replacement=with_replacement),
                connections,  with_replacement, conn_type="total")

    def test_total_connector_too_many(self):
        self.runsafe(self.total_connector_too_many)

    def multiple_connectors(self):
        n_destinations = 5
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)
        input_pop = sim.Population(SOURCES, sim.SpikeSourceArray(
            spike_times=[[0], [20], [40], [60], [80]]), label="input_pop")
        destination = sim.Population(
            n_destinations, sim.IF_curr_exp(
                tau_syn_E=1, tau_refrac=0,  tau_m=1), label="destination")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        sim.Projection(
            input_pop, destination, sim.OneToOneConnector(),
            synapse_type=synapse_type)
        sim.Projection(
            input_pop, destination, sim.AllToAllConnector(),
            synapse_type=synapse_type)
        destination.record("v")
        sim.run(100)
        neo = destination.get_data(["v"])
        v = neo.segments[0].filter(name="v")[0]  # pylint: disable=no-member
        counts = self.calc_spikes_received(v)
        for i, count in enumerate(counts):
            for j in range(n_destinations):
                if i == j:
                    self.assertEqual(count[j], 2)
                else:
                    self.assertEqual(count[j], 1)
        sim.end()

    def test_multiple_connectors(self):
        self.runsafe(self.multiple_connectors)

    def onetoone_population_views(self):
        sim.setup(timestep=1.0)
        in_pop = sim.Population(4, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        conn = sim.Projection(in_pop[1:3], pop[2:4], sim.OneToOneConnector(),
                              sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        target = [[1, 2, 0.5, 2.], [2, 3, 0.5, 2.]]
        self.assertCountEqual(weights, target)

    def test_onetoone_population_views(self):
        self.runsafe(self.onetoone_population_views)

    def onetoone_multicore_population_views(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 10)
        sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, 10)
        in_pop = sim.Population(14, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(17, sim.IF_curr_exp(), label="pop")
        conn = sim.Projection(in_pop[6:12], pop[9:16], sim.OneToOneConnector(),
                              sim.StaticSynapse(weight=0.5, delay=2),
                              label="test")
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        # Check the connections are correct
        target = [[6, 9, 0.5, 2.], [7, 10, 0.5, 2.], [8, 11, 0.5, 2.],
                  [9, 12, 0.5, 2.], [10, 13, 0.5, 2.], [11, 14, 0.5, 2.]]
        self.assertCountEqual(weights, target)

    def fixedprob_population_views(self):
        sim.setup(timestep=1.0)
        in_pop = sim.Population(4, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        rng = NumpyRNG(seed=1)
        conn = sim.Projection(in_pop[1:3], pop[2:4],
                              sim.FixedProbabilityConnector(0.5, rng=rng),
                              sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        # The fixed seed means this gives the same answer each time
        target = [[1, 3, 0.5, 2.], [2, 2, 0.5, 2.], [2, 3, 0.5, 2]]
        self.assertCountEqual(weights, target)

    def test_fixedprob_population_views(self):
        self.runsafe(self.fixedprob_population_views)

    def fixedpre_population_views(self):
        sim.setup(timestep=1.0)
        in_pop = sim.Population(4, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        rng = NumpyRNG(seed=2)
        conn = sim.Projection(in_pop[0:3], pop[1:4],
                              sim.FixedNumberPreConnector(2, rng=rng),
                              sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        # The fixed seed means this gives the same answer each time
        target = [[1, 1, 0.5, 2.0], [1, 2, 0.5, 2.0], [1, 3, 0.5, 2.0],
                  [2, 1, 0.5, 2.0], [2, 2, 0.5, 2.0], [2, 3, 0.5, 2.0]]
        self.assertCountEqual(weights, target)

    def test_fixedpre_population_views(self):
        self.runsafe(self.fixedpre_population_views)

    def fixedpost_population_views(self):
        sim.setup(timestep=1.0)
        in_pop = sim.Population(4, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        rng = NumpyRNG(seed=1)
        conn = sim.Projection(in_pop[0:3], pop[1:4],
                              sim.FixedNumberPostConnector(2, rng=rng),
                              sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        # The fixed seed means this gives the same answer each time
        target = [[0, 1, 0.5, 2.0], [0, 3, 0.5, 2.0], [1, 1, 0.5, 2.0],
                  [1, 3, 0.5, 2.0], [2, 1, 0.5, 2.0], [2, 2, 0.5, 2.0]]
        self.assertCountEqual(weights, target)

    def test_fixedpost_population_views(self):
        self.runsafe(self.fixedpost_population_views)

    def fixedtotal_population_views(self):
        sim.setup(timestep=1.0)
        in_pop = sim.Population(4, sim.SpikeSourceArray([0]), label="in_pop")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        rng = NumpyRNG(seed=1)
        n_conns = 5
        conn = sim.Projection(in_pop[0:3], pop[1:4],
                              sim.FixedTotalNumberConnector(
                                  n_conns, with_replacement=False, rng=rng),
                              sim.StaticSynapse(weight=0.5, delay=2))
        conn2 = sim.Projection(in_pop[0:3], pop[1:4],
                               sim.FixedTotalNumberConnector(
                                   n_conns, with_replacement=True, rng=rng),
                               sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        weights2 = conn2.get(['weight', 'delay'], 'list')
        sim.end()
        # The fixed seed means this gives the same answer each time
        target = [[0, 2, 0.5, 2.0], [0, 3, 0.5, 2.0], [1, 1, 0.5, 2.0],
                  [1, 3, 0.5, 2.0], [2, 1, 0.5, 2.0]]
        target2 = [[0, 2, 0.5, 2.0], [0, 2, 0.5, 2.0], [1, 1, 0.5, 2.0],
                   [2, 2, 0.5, 2.0], [2, 3, 0.5, 2.0]]
        self.assertCountEqual(weights, target)
        self.assertEqual(len(weights), n_conns)
        self.assertCountEqual(weights2, target2)
        self.assertEqual(len(weights2), n_conns)

    def test_fixedtotal_population_views(self):
        self.runsafe(self.fixedtotal_population_views)
