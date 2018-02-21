from spinn_front_end_common.utilities import globals_variables
import numpy
from spynnaker.pyNN.utilities.spynnaker_failed_state \
    import SpynnakerFailedState


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

    def is_a_pynn_random(self, values):
        return isinstance(values, MockRNG)

    def get_pynn_NumpyRNG(self):
        return MockRNG()

    @classmethod
    def setup(cls):
        simulator = MockSimulator()
        globals_variables.set_failed_state(SpynnakerFailedState())
        globals_variables.set_simulator(simulator)
