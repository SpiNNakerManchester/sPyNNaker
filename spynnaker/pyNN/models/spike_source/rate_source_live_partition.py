import math

from .rate_source_live_vertex import RateSourceLiveVertex
from .rate_live_injector_vertex import RateLiveInjectorVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides

from pacman.model.graphs.application.application_edge \
    import ApplicationEdge

from spynnaker.pyNN.utilities import constants

import numpy as np

# The number of usable application cores in a chip
APP_CORES_PER_CHIP = 15

# Needs to be 1, 2, 4 or 8 under the current implementation
N_CHIPS = 2

class RateSourceLivePartition(SimplePopulationSettable, AbstractChangableAfterRun):

    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions",
        "__refresh_rate",
        "__injector_vertices",
        "__atoms_per_partition",
        "__machine_vertices",
        "__dataset",
        "__subsets",
        "__packet_compressor",
        "__dataset_len",
        "__epochs"]

    def __init__(
        self, sources, constraints, label, rate_source_live,
        partitions, refresh_rate, dataset, packet_compressor,
        dataset_len, epochs):

        self.__n_atoms = sources
        self.__vertices = [list() for _ in range(partitions)]
        self.__partitions = partitions
        self.__refresh_rate = refresh_rate
        self.__dataset = dataset
        self.__injector_vertices = list()
        self.__packet_compressor = packet_compressor
        self.__dataset_len = dataset_len
        self.__epochs = epochs

        subset_length = int(len(self.__dataset[0]) / N_CHIPS)

        # Partition by column the dataset according to the number of chips we want to use
        self.__subsets = np.hsplit(np.array(self.__dataset), N_CHIPS)

        # The number of generators inside a partition
        self.__atoms_per_partition = self._compute_partition_and_offset_size(self.__n_atoms)

        # Keep one core in the chip as service core to inject the values in memory
        self.__machine_vertices = self._compute_partition_and_offset_size((APP_CORES_PER_CHIP - 1) * N_CHIPS)

        for chip in range(N_CHIPS):
            
            self.__injector_vertices.append(RateLiveInjectorVertex(
                int(self.__n_atoms / N_CHIPS), "Rate_live_injector",
                constraints, rate_source_live, self.__subsets[chip][1:],
                refresh_rate, self.__dataset_len, epochs))
    
            vertex_offset = 0
            atoms_partition_offset = 0
            # List of app vertices in a single partition
            generator_vertices = list()
        
            for i in range(self.__partitions):

                # List of lists containing the values to be used on the first ts for each machine vertex
                starting_slices = []
                start = vertex_offset
                # Total number of generators in the vertices of this partition on this chip
                partitions_atoms = int(self.__atoms_per_partition[i] / N_CHIPS)
                atoms_partition_offset += partitions_atoms
                # Number of machine vertices of this partition on this chip
                machine_vertices = int(self.__machine_vertices[i] / N_CHIPS)
                # Set this in order to force the partitioning to have the number of machine cores we want
                max_atoms_per_core = int(math.ceil(partitions_atoms / machine_vertices))
            
                for v in range(machine_vertices):

                    if v < machine_vertices - 1:
                        starting_slices.append(self.__subsets[chip][0][start : (start + max_atoms_per_core)])
                        start += max_atoms_per_core 
                    else:
                        starting_slices.append(self.__subsets[chip][0][start : atoms_partition_offset])

                source_vertex = RateSourceLiveVertex(
                    partitions_atoms, constraints, max_atoms_per_core,
                    label+"_chip_"+str(chip)+"_p"+str(i), rate_source_live, machine_vertices, self.__refresh_rate,
                    self.__injector_vertices[chip], vertex_offset, starting_slices, self.__packet_compressor)

                self.__vertices[i].append(source_vertex)
                generator_vertices.append(source_vertex)

                vertex_offset += partitions_atoms

            self.__injector_vertices[chip].connected_app_vertices = generator_vertices

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    @property
    def partitions(self):
        return self.__partitions

    def add_internal_edges_and_vertices(self, spinnaker_control):

        for chip in range(N_CHIPS):

            spinnaker_control.add_application_vertex(self.__injector_vertices[chip])

            for partition in range(self.__partitions):

                spinnaker_control.add_application_vertex(self.__vertices[partition][chip])

                spinnaker_control.add_application_edge(ApplicationEdge(
                    self.__injector_vertices[chip], self.__vertices[partition][chip],
                    label="injector_edge {}".format(spinnaker_control.none_labelled_edge_count)),
                    constants.SPIKE_PARTITION_ID)
                spinnaker_control.increment_none_labelled_edge_count()

    @property
    def injector_vertices(self):
        return self.__injector_vertices

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
        return self.__vertices[0][0].requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        for i in range(self.__partitions):
            for j in range(N_CHIPS):
                self.__vertices[i][j].requires_mapping = False