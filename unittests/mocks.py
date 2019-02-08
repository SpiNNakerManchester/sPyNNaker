import configparser
import numpy
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)


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


class MockRNG(object):

    def next(self, n):
        return numpy.random.uniform(size=n)


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

    def is_a_pynn_random(self, values):
        return isinstance(values, MockRNG)

    def get_pynn_NumpyRNG(self):
        return MockRNG()

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
