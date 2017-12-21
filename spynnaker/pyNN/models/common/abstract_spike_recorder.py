from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSpikeRecorder(object):
    """
    Interface to make sure the direct spike classes have all the required
    methods
    """

    __slots__ = ()

    @abstractmethod
    def record(self, record):
        pass

    @abstractmethod
    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        pass

    @abstractmethod
    def get_dtcm_usage_in_bytes(self):
        pass

    @abstractmethod
    def get_n_cpu_cycles(self, n_neurons):
        pass

    @abstractmethod
    def get_spikes(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):
        pass

    @abstractmethod
    def get_spikes_sampling_interval(self):
        pass
