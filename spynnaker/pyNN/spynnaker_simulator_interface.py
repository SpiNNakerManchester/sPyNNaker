from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty
from spinn_utilities.abstract_base import abstractmethod

from spinn_front_end_common.utilities.simulator_interface \
    import SimulatorInterface

# chrsitian, remove runtime callbacks, reset stuff, stop, get_current_time,
# might need to go down or up

@add_metaclass(AbstractBase)
class SpynnakerSimulatorInterface(SimulatorInterface):

    __slots__ = ()

    @abstractproperty
    def has_reset_last(self):
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
    def use_virtual_board(self):
        pass

    @abstractmethod
    def run(self, simtime, callbacks=None):
        pass

    @abstractmethod
    def reset(self, annotations=None):
        pass

    @abstractmethod
    def get_current_time(self):
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

    @abstractmethod
    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        pass
