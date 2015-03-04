from pacman.model.constraints.key_allocator_contiguous_range_constraint import \
    KeyAllocatorContiguousRangeContraint
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex

from enum import Enum
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSpikeSource(AbstractPopulationVertex, AbstractDataSpecableVertex):

    _SPIKE_SOURCE_REGIONS = Enum(
        value="_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('BLOCK_INDEX_REGION', 1),
               ('SPIKE_DATA_REGION', 2),
               ('SPIKE_HISTORY_REGION', 3)])

    def __init__(self, label, n_neurons, constraints, max_atoms_per_core,
                 machine_time_step, timescale_factor):
        AbstractPopulationVertex.__init__(
            self, label=label, n_neurons=n_neurons, constraints=constraints,
            machine_time_step=machine_time_step,
            max_atoms_per_core=max_atoms_per_core,
            timescale_factor=timescale_factor)
        AbstractDataSpecableVertex.__init__(
            self, label=label, n_atoms=n_neurons,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)

    @abstractmethod
    def is_abstract_spike_source(self):
        """ helper method for is_instance

        :return:
        """

    def retrieve_edge_constraints_for_receivers(self):
        return self._retrieve_data_specable_edge_constraints_for_receivers()

    def retrieve_edge_constraints_for_senders(self):
        return self._retrieve_data_specable_edge_constraints_for_senders()

    def __str__(self):
        return "spike source with atoms {}".format(self.n_atoms)

    def __repr__(self):
        return self.__str__()