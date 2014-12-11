from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex import AbstractPartitionableVertex

from enum import Enum


class AbstractSpikeSource(
        AbstractRecordableVertex, AbstractPartitionableVertex,
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
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        AbstractRecordableVertex.__init__(self, machine_time_step, label)

    def __str__(self):
        return "spike source with atoms {}".format(self.n_atoms)

    def __repr__(self):
        return self.__str__()
