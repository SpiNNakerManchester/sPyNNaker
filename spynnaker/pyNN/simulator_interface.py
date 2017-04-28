from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractmethod

@add_metaclass(AbstractBase)
class SimulatorInterface(object):

    __slots__ = ()

    @abstractmethod
    def run(self, simtime, callbacks=None):
        pass

    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def reset(self, annotations=None):
        pass

    @abstractmethod
    def run_until(self, time_point, callbacks=None):
        pass

    @abstractmethod
    def run_for(self, simtime, callbacks=None):
        pass

    @abstractmethod
    def get_current_time(self):
        pass

    @abstractmethod
    def get_time_step(self):
        pass

    @abstractmethod
    def get_min_delay(self):
        pass

    @abstractmethod
    def get_max_delay(self):
        pass

    @abstractmethod
    def num_processes(self):
        pass

    @abstractmethod
    def rank(self):
        pass

    @abstractmethod
    def initialize(self, cells, **initial_values):
        pass

    @abstractmethod
    def create(self, cellclass, cellparams=None, n=1):
        pass

    @abstractmethod
    def connect(self, pre, post, weight=0.0, delay=None, receptor_type=None,
                p=1, rng=None):
        pass

    @abstractmethod
    def record(self, variables, source, filename, sampling_interval=None,
               annotations=None):
        pass

    @abstractmethod
    def min_delay(self):
        pass

    @abstractmethod
    def is_a_pynn_random(self, thing):
        """
        Checks if the thing is a pynn random

        The exact definition of a pynn random can or could change between
        pynn versions so can only be checked against a specific pynn version

        :param thing: any object
        :return: True if this object is a pynn random
        :trype: bol
        """
        pass

    @abstractmethod
    def get_pynn_NumpyRNG(self):
        pass
