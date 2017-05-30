from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty
from spinn_utilities.abstract_base import abstractmethod

from spinn_front_end_common.utilities.simulator_interface \
    import SimulatorInterface


@add_metaclass(AbstractBase)
class SpynnakerSimulatorInterface(SimulatorInterface):

    __slots__ = ()

    # Used at common level but depends on PyNN so individual implementations
    @abstractmethod
    def get_distribution_to_stats(self):
        pass

    # Implemented in FEC but only used by spynakker
    @abstractmethod
    def get_current_time(self):
        pass

    # Used at common level but depends on PyNN so individual implementations
    @abstractmethod
    def get_pynn_NumpyRNG(self):
        pass

    # declared in common and used in common
    @abstractproperty
    def has_reset_last(self):
        pass

    # Used at common level but depends on PyNN so individual implementations
    @abstractmethod
    def is_a_pynn_random(self, thing):
         pass

    # declared in FEC common and used in 7 and 8
    @abstractproperty
    def max_delay(self):
        pass

    # declared in FEC common and used in 7 and 8
    @abstractproperty
    def min_delay(self):
        pass

    # declared in 7 and 8 and used in 7 and 8 (could be moved up)
    @abstractmethod
    def reset(self, annotations=None):
        pass

    # declared in 7 and 8 and used in 7 and 8 (could be moved up)
    @abstractmethod
    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        pass

