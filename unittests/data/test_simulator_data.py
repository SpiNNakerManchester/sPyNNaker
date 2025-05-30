# Copyright (c) 2021 The University of Manchester
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

import unittest
from spinn_utilities.exceptions import (
    DataNotYetAvialable, SimulatorRunningException)
from spinn_front_end_common.utilities.exceptions import (
    ConfigurationException)
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from spynnaker.pyNN.models.neuron.builds import IFCurrExpBase
from spynnaker.pyNN.models.projection import Projection
from spynnaker.pyNN.models.populations.population import Population
import pyNN.spiNNaker as sim


class TestSimulatorData(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    def test_setup(self) -> None:
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        writer = SpynnakerDataWriter.setup()
        self.assertIn("run_1", SpynnakerDataView.get_run_dir_path())
        with self.assertRaises(DataNotYetAvialable):
            SpynnakerDataView.get_simulation_time_step_us()
        with self.assertRaises(DataNotYetAvialable):
            SpynnakerDataView.get_min_delay()
        self.assertFalse(SpynnakerDataView.has_min_delay())
        writer.set_up_timings(100, 10)
        self.assertTrue(SpynnakerDataView.has_min_delay())
        self.assertEqual(100,  SpynnakerDataView.get_simulation_time_step_us())
        self.assertEqual(0.1, SpynnakerDataView.get_min_delay())

    def test_min_delay(self) -> None:
        writer = SpynnakerDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            SpynnakerDataView.get_min_delay()

        writer.set_up_timings_and_delay(500, 1, 0.5)
        self.assertEqual(0.5, SpynnakerDataView.get_min_delay())

        writer.set_up_timings_and_delay(1000, 1, None)
        self.assertEqual(1, SpynnakerDataView.get_min_delay())

        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(1000, 1, 0)

        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(1000, 1, 1.5)

        writer.set_up_timings_and_delay(1000, 1, 2)
        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(2000, 1, 1)

        with self.assertRaises(TypeError):
            writer.set_up_timings_and_delay(
                1000, 1, "baocn")  # type: ignore[arg-type]

    def test_mock(self) -> None:
        # check there is a value not what it is
        self.assertIsNotNone(SpynnakerDataView.get_app_id())
        self.assertIsNotNone(SpynnakerDataView.get_min_delay())

    def test_populations_and_projections(self) -> None:
        writer = SpynnakerDataWriter.setup()
        writer.set_up_timings_and_delay(1000, 1, 1)
        self.assertListEqual(
            [], list(SpynnakerDataView.iterate_populations()))
        self.assertEqual(0, SpynnakerDataView.get_n_populations())
        self.assertListEqual(
            [], list(SpynnakerDataView.iterate_projections()))
        self.assertEqual(0, SpynnakerDataView.get_n_projections())
        model = IFCurrExpBase()
        pop_1 = Population(size=5, cellclass=model)
        # Population adds itself so no one can
        with self.assertRaises(NotImplementedError):
            writer.add_population(pop_1)
        self.assertListEqual(
            [pop_1], list(SpynnakerDataView.iterate_populations()))
        self.assertEqual(1, SpynnakerDataView.get_n_populations())
        self.assertEqual(5, writer._get_id_counter())
        pop_2 = Population(size=15, cellclass=model)

        self.assertListEqual([pop_1, pop_2], sorted(
            SpynnakerDataView.iterate_populations(), key=lambda x: x.label))
        self.assertEqual(2, SpynnakerDataView.get_n_populations())
        self.assertEqual(20, writer._get_id_counter())
        pro_1 = Projection(
            pop_1, pop_2, OneToOneConnector(), receptor_type='excitatory')
        self.assertListEqual(
            [pro_1], list(SpynnakerDataView.iterate_projections()))
        self.assertEqual(1, SpynnakerDataView.get_n_projections())
        pro_2 = Projection(
            pop_2, pop_1, OneToOneConnector(), receptor_type='excitatory')
        self.assertListEqual([pro_1, pro_2], sorted(
            SpynnakerDataView.iterate_projections(), key=lambda x: x.label))
        self.assertEqual(2, SpynnakerDataView.get_n_projections())
        writer.start_run()
        # Unable to add while running
        with self.assertRaises(SimulatorRunningException):
            Population(size=11, cellclass=model)
        with self.assertRaises(SimulatorRunningException):
            Projection(
                pop_2, pop_1, OneToOneConnector(), receptor_type="inhibitory")
        writer.finish_run()
        writer.hard_reset()
        # population not changed by hard reset
        self.assertListEqual([pop_1, pop_2], sorted(
            SpynnakerDataView.iterate_populations(), key=lambda x: x.label))
        self.assertEqual(2, SpynnakerDataView.get_n_populations())
        self.assertListEqual([pro_1, pro_2], sorted(
            SpynnakerDataView.iterate_projections(), key=lambda x: x.label))
        self.assertEqual(2, SpynnakerDataView.get_n_projections())
        self.assertEqual(20, writer._get_id_counter())
        with self.assertRaises(TypeError):
            writer.add_population("bacon")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            writer.add_projection("bacon")  # type: ignore[arg-type]

    def test_sim_name(self) -> None:
        self.assertEqual(SpynnakerDataView.get_sim_name(), sim.name())
        self.assertIn("sPyNNaker", SpynnakerDataView.get_sim_name())
