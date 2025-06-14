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

import os
from unittest.case import SkipTest
from requests.exceptions import ConnectionError

from spinn_utilities.config_holder import (
    config_options, config_sections, get_report_path, get_timestamp_path)

from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.config_setup import cfg_paths_skipped
import pyNN.spiNNaker as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """

    def assert_reports(self) -> None:
        skipped = cfg_paths_skipped()
        for section in config_sections():
            for option in config_options(section):
                if option in skipped:
                    continue
                if option.startswith("path"):
                    path = get_report_path(section=section, option=option)
                elif option.startswith("tpath"):
                    path = get_timestamp_path(section=section, option=option)
                else:
                    continue
                print(f"found {option} at {path}")
                if not os.path.exists(path):
                    raise AssertionError(
                        f"Unable to find report for {option} {path}")

    def debug(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(100, sim.IF_curr_exp, {}, label="pop")
        pop.record("v")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        try:
            sim.run(0)
        except ConnectionError:
            raise SkipTest("DNS Error Monster!")

        pop.get_data("v")
        self.assert_reports()

        sim.run(10)  # second run
        pop.get_data("v")

        sim.end()
