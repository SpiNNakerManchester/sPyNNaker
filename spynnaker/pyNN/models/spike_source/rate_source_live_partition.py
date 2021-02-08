import math

from .rate_source_live_vertex import RateSourceLiveVertex
from .rate_live_injector_vertex import RateLiveInjectorVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides

# The number of usable application cores in a chip
APP_CORES_PER_CHIP = 15

class RateSourceLivePartition(SimplePopulationSettable, AbstractChangableAfterRun):

    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions",
        "__refresh_rate",
        "__injector_vertex"]

    def __init__(self, sources, constraints, label, rate_source_live, partitions, refresh_rate):

        self.__n_atoms = sources
        self.__vertices = list()
        self.__partitions = partitions
        self.__refresh_rate = refresh_rate

        self.__injector_vertex = RateLiveInjectorVertex(self.__n_atoms, "Rate_live_injector", constraints, rate_source_live)
        
        self.__atoms_per_partition = self._compute_partition_and_offset_size(self.__n_atoms)
    
        # Keep one core in the chip as service core to inject the values in memory
        self.__machine_vertices = self._compute_partition_and_offset_size(APP_CORES_PER_CHIP - 1)

        # Set this in order to force the partitioning to have the number of machine cores we want
        self.__max_atoms_per_core = int(math.ceil(self.__atoms_per_partition / self.__machine_vertices))

        vertex_offset = 0
        
        for i in range(self.__partitions):
            self.__vertices.append(RateSourceLiveVertex(
                self.__atoms_per_partition[i], constraints, self.__max_atoms_per_core,
                label+str(i), rate_source_live, self.__machine_vertices[i], self.__refresh_rate,
                self.__injector_vertex, vertex_offset))

            vertex_offset += self.__atoms_per_partition[i]

        self.__injector_vertex.connected_app_vertices = self.__vertices

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    @property
    def injector_vertex(self):
        return self.__injector_vertex

    def _compute_partition_and_offset_size(self, elements):

        min_elements_per_partition = int(math.floor(elements / self.__partitions))

        remainder = elements % self.__partitions

        contents = [min_elements_per_partition + 1 if i < remainder 
            else min_elements_per_partition for i in range(self.__partitions)]

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