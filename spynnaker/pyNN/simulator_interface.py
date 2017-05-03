from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty
from spinn_utilities.abstract_base import abstractmethod


@add_metaclass(AbstractBase)
class SimulatorInterface(object):

    __slots__ = ()

    @abstractproperty
    def graph_mapper(self):
        pass

    @abstractproperty
    def has_reset_last(self):
        pass

    @abstractproperty
    def has_ran(self):
        pass

    @abstractproperty
    def increment_none_labelled_vertex_count(self):
        pass

    @abstractproperty
    def placements(self):
        pass

    @abstractproperty
    def machine_time_step(self):
        pass

    @abstractproperty
    def max_supported_delay(self):
        pass

    @abstractproperty
    def min_supported_delay(self):
        pass

    @abstractproperty
    def none_labelled_vertex_count(self):
        pass

    @abstractproperty
    def transceiver(self):
        pass

    @abstractproperty
    def use_virtual_board(self):
        pass

    @abstractmethod
    def run(self, simtime, callbacks=None):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def reset(self, annotations=None):
        pass

    @abstractmethod
    def get_current_time(self):
        pass

    @abstractmethod
    def _add_socket_address(self, x):
        pass

    @abstractmethod
    def create_population(self, size, cellclass, cellparams, structure,
                          label):
        pass

    @abstractmethod
    def create_projection(self, presynaptic_population,
                          postsynaptic_population, connector, source,
                          target, synapse_dynamics, label, rng):
        pass

    @abstractmethod
    def get_distribution_to_stats(self):
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
