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
import numpy
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)
from builtins import property


class MockPopulation(object):

    def __init__(self, size, label):
        self._size = size
        self._label = label

    @property
    def size(self):
        return self._size

    @property
    def label(self):
        return self.label

    def __repr__(self):
        return "Population {}".format(self._label)


class MockSynapseInfo(object):

    def __init__(self, pre_population, post_population, weights, delays):
        self._pre_population = pre_population
        self._post_population = post_population
        self._weights = weights
        self._delays = delays

    @property
    def pre_population(self):
        return self._pre_population

    @property
    def post_population(self):
        return self._post_population

    @property
    def n_pre_neurons(self):
        return self._pre_population.size

    @property
    def n_post_neurons(self):
        return self._post_population.size

    @property
    def weights(self):
        return self._weights

    @property
    def delays(self):
        return self._delays


class MockRNG(object):

    def __init__(self):
        self._rng = numpy.random.RandomState()

    def next(self, n):
        return self._rng.uniform(size=n)

    def __getattr__(self, name):
        return getattr(self._rng, name)


class MockSimulator(object):

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config["Simulation"] = \
            {"spikes_per_second": "30",
             "incoming_spike_buffer_size": "256",
             "ring_buffer_sigma": "5",
             "one_to_one_connection_dtcm_max_bytes": "0"}
        self.config["Buffers"] = {"time_between_requests": "10",
                                  "minimum_buffer_sdram": "10",
                                  "use_auto_pause_and_resume": "True",
                                  "receive_buffer_host": "None",
                                  "receive_buffer_port": "None",
                                  "enable_buffered_recording": "False"}
        self.config["MasterPopTable"] = {"generator": "BinarySearch"}
        self.config["Reports"] = {"n_profile_samples": 0}

    def add_population(self, pop):
        pass

    def add_application_vertex(self, vertex):
        pass

    def verify_not_running(self):
        pass

    def has_ran(self):
        return False

    def has_reset_last(self):
        return False

    @property
    def machine_time_step(self):
        return 1000

    @property
    def id_counter(self):
        return 1

    @id_counter.setter
    def id_counter(self, value):
        pass

    @classmethod
    def setup(cls):
        simulator = MockSimulator()
        globals_variables.set_failed_state(SpynnakerFailedState())
        globals_variables.set_simulator(simulator)
        return simulator

    @property
    def use_virtual_board(self):
        return True
