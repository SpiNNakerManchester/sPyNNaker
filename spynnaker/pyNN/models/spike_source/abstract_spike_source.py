from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex \
    import AbstractRecordableVertex
from pacman.model.abstract_classes.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex

from enum import Enum
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSpikeSource(AbstractRecordableVertex,
                          AbstractPartitionableVertex,
                          AbstractDataSpecableVertex):

    _SPIKE_SOURCE_REGIONS = Enum(
        value="_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('BLOCK_INDEX_REGION', 1),
               ('SPIKE_DATA_REGION', 2),
               ('SPIKE_HISTORY_REGION', 3)])

    def __init__(self, label, n_neurons, constraints, max_atoms_per_core,
                 machine_time_step, timescale_factor):
        AbstractDataSpecableVertex.__init__(
            self, label=label, n_atoms=n_neurons,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractRecordableVertex.__init__(self, machine_time_step, label)
        AbstractPartitionableVertex.__init__(
            self, n_neurons, label, max_atoms_per_core, constraints)

    @abstractmethod
    def is_abstract_spike_source(self):
        """ helper method for is_instance

        :return:
        """

    def __str__(self):
        return "spike source with atoms {}".format(self.n_atoms)

    def __repr__(self):
        return self.__str__()
