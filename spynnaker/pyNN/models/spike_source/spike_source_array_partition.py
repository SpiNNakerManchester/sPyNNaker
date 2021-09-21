import sys
from .spike_source_array_vertex import SpikeSourceArrayVertex
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, SimplePopulationSettable)


DEFAULT_MAX_ATOMS_PER_NEURON_CORE = 64


class SpikeSourceArrayPartition(ReverseIpTagMultiCastSource, AbstractSpikeRecordable,
                                SimplePopulationSettable, AbstractChangableAfterRun,
                                ProvidesKeyToAtomMappingImpl):
    __slots__ = [
        "_vertices",
        "_n_atoms",
        "_offset",
        "_n_partitions"]

    def __init__(self, n_neurons, spike_times, constraints, label, max_atoms, spike_source_array):

        self._n_atoms = n_neurons
        self._vertices = list()

        self._n_partitions = 1
        #if self._n_atoms > DEFAULT_MAX_ATOMS_PER_NEURON_CORE:
        #    self._n_partitions = 2
        #else:
        #    self._n_partitions = 1

        #self._offset = self._compute_partition_and_offset_size()

        for i in range(self._n_partitions):
            # Distribute neurons in order to have the low neuron cores completely filled
            atoms = self._n_atoms
            #atoms = self._offset if (self._n_atoms - (self._offset * (i + 1)) >= 0) \
            #    else self._n_atoms - (self._offset * i)

            self._vertices.append(SpikeSourceArrayVertex(
                atoms, spike_times, constraints, label+"_"+str(i), max_atoms, spike_source_array))

    @property
    def n_atoms(self):
        return self._n_atoms

    @property
    def out_vertices(self):
        return self._vertices

    def mark_no_changes(self):
        for i in range(self._n_partitions):
            self._vertices[i].mark_no_changes()

    @property
    def requires_mapping(self):
        return self._vertices[0].requires_mapping

    @property
    def spike_times(self):
        return self._spike_times

    @spike_times.setter
    def spike_times(self, spike_times):
        for i in range(self._n_partitions):
            self._vertices[i].spike_times = spike_times

    def _compute_partition_and_offset_size(self):

        return -((-self._n_atoms / self._n_partitions) // DEFAULT_MAX_ATOMS_PER_NEURON_CORE) * DEFAULT_MAX_ATOMS_PER_NEURON_CORE


    def is_recording_spikes(self):
        return self._vertices[0].is_recording_spikes()

    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        for i in range(self._n_partitions):
            self._vertices[i].set_recording_spikes(new_state, sampling_interval, indexes)

    def get_spikes_sampling_interval(self):
        return self._vertices[0].get_spikes_sampling_interval()

    def get_spikes(self):
        # TODO
        return None

    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        for i in range(self._n_partitions):
            self._vertices[i].clear_spike_recording(buffer_manager, placements, graph_mapper)

    def set_model_max_atoms_per_core(self, new_value=sys.maxsize):
        for i in range(self._n_partitions):
            self._vertices[i].set_model_max_atoms_per_core(new_value)

    def describe(self):
        # TODO
        return None