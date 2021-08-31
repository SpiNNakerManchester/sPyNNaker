from .rate_source_multiple_vertex import RateSourceMultipleVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides
import math

class RateSourceMultiplePartition(SimplePopulationSettable, AbstractChangableAfterRun):


    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions",
        "__max_atoms_per_core",
        "__atoms_per_partition"]

    def __init__(self, n_neurons, constraints, label, max_atoms, rate_source_multiple, partitions):

        self.__n_atoms = n_neurons
        self.__vertices = list()
        self.__partitions = self.__n_atoms if self.__n_atoms <= partitions else partitions

        # The number of generators inside a partition
        self.__atoms_per_partition = self._compute_partition_and_offset_size(self.__n_atoms)

        for i in range(self.__partitions):
            self.__vertices.append(RateSourceMultipleVertex(
                self.__atoms_per_partition[i], constraints,
                label+str(i), max_atoms, rate_source_multiple))

        [self.__vertices[i].connected_vertices(self.__vertices) for i in range(len(self.__vertices))]


    def _compute_partition_and_offset_size(self, elements):

        min_elements_per_partition = int(math.floor(elements / self.__partitions))

        remainder = elements % self.__partitions

        contents = [min_elements_per_partition + 1 if i < remainder
            else min_elements_per_partition for i in range(self.__partitions)]

        return contents

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self.__change_requires_neuron_parameters_reload = True

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__vertices[0].requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        for i in range(self.__partitions):
            self.__vertices[i].requires_mapping = False