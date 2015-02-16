from pacman.model.constraints.key_allocator_fixed_mask_constraint import \
    KeyAllocatorFixedMaskConstraint
from pacman.utilities import constants as pacman_constants

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex import AbstractPartitionableVertex

from enum import Enum
from spynnaker.pyNN.models.partitioned_models.\
    partitioned_population_vertex import PartitionedPopulationVertex


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
        self.add_constraint(KeyAllocatorFixedMaskConstraint(
            pacman_constants.DEFAULT_MASK))

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         additional_constraints=list()):
        """ overloaded from abstract_partitionable_vertex so that partitioned
        vertices has a n_atoms (used in key-allocator algorithums)

        :param vertex_slice: the slice of atoms from the partitionable vertex
        to the partitioned vertex
        :param resources_required: the resources used by thsi partitioned vertex
        :param label: the string represnetation of this vertex
        :param additional_constraints: any additional constraints used by
        future mapping algorithums.
        :return: a instance of a partitioned_vertex
        """
        partitioned_vertex = PartitionedPopulationVertex(
            n_atoms=vertex_slice.n_atoms, label=label,
            resources_required=resources_required,
            constraints=additional_constraints)
        return partitioned_vertex

    def __str__(self):
        return "spike source with atoms {}".format(self.n_atoms)

    def __repr__(self):
        return self.__str__()
