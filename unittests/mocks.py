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

import configparser
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities import globals_variables
from spynnaker8.spinnaker import Spynnaker8FailedState
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon


class MockPopulation(object):

    def __init__(self, size, label):
        self._size = size
        self._label = label

    @property
    @overrides(Population.size)
    def size(self):
        return self._size

    @property
    @overrides(Population.label)
    def label(self):
        return self.label

    def __repr__(self):
        return "Population {}".format(self._label)


class MockSimulator(object):

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config["Simulation"] = \
            {"spikes_per_second": "30",
             "incoming_spike_buffer_size": "256",
             "ring_buffer_sigma": "5",
             "one_to_one_connection_dtcm_max_bytes": "0",
             "drop_late_spikes": True,
             }
        self.config["Reports"] = {"n_profile_samples": 0}

    @overrides(AbstractSpiNNakerCommon.add_population)
    def add_population(self, population):
        pass

    @overrides(AbstractSpiNNakerCommon.add_application_vertex)
    def add_application_vertex(self, vertex):
        pass

    @overrides(AbstractSpiNNakerCommon.verify_not_running)
    def verify_not_running(self):
        pass

    @overrides(AbstractSpiNNakerCommon.has_ran)
    def has_ran(self):
        return False

    @overrides(AbstractSpiNNakerCommon.has_reset_last)
    def has_reset_last(self):
        return False

    @property
    @overrides(AbstractSpiNNakerCommon.machine_time_step)
    def machine_time_step(self):
        return 1000

    @property
    @overrides(AbstractSpiNNakerCommon.id_counter)
    def id_counter(self):
       return 1

    @id_counter.setter
    #overrides(AbstractSpiNNakerCommon.id_counter)
    def id_counter(self, value):
        pass

    @classmethod
    def setup(cls, init_failed_state=False):
        simulator = MockSimulator()
        if init_failed_state:
            globals_variables.set_failed_state(Spynnaker8FailedState())
        globals_variables.set_simulator(simulator)
        return simulator

    @property
    @overrides(AbstractSpiNNakerCommon.min_delay)
    def min_delay(self):
       return 1

    @property
    @overrides(AbstractSpiNNakerCommon.t)
    def t(self):
        return 0
