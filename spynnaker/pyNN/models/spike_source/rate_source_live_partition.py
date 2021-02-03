import math

from .rate_source_live_vertex import RateSourceLiveVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides

class RateSourceLivePartition(SimplePopulationSettable, AbstractChangableAfterRun):

    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions"]

    def __init__(self, sources,
        constraints, label, max_atoms, rate_source_live, partitions):

        self.__n_atoms = sources
        self.__vertices = list()
        self.__partitions = partitions

        self.__atoms_per_partition = self._compute_partition_and_offset_size()

        for i in range(self.__partitions):
            self.__vertices.append(RateSourceLiveVertex(
                self.__atoms_per_partition[i], constraints,
                label+str(i), max_atoms, rate_source_live))

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    def _compute_partition_and_offset_size(self):

        min_neurons_per_partition = int(math.floor(self._n_atoms / self.__partitions))

        remaining_neurons = self._n_atoms - (min_neurons_per_partition * self.__partitions)

        contents = [min_neurons_per_partition if i < self.__partitions 
            else min_neurons_per_partition + remaining_neurons 
            for i in range(self.__partitions)]

        return contents

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