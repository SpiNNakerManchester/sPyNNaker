from pacman.model.decorators import overrides
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils
from .abstract_spike_recorder import AbstractSpikeRecorder

import math
import numpy
import logging

logger = logging.getLogger(__name__)

BYTES_PER_WORD = 4


class SpikeRecorder(AbstractSpikeRecorder):

    def __init__(self):
        self._sampling_rate = 0

    @property
    def record(self):
        return self._sampling_rate != 0

    @overrides(AbstractSpikeRecorder.set_recording)
    def set_recording(self, new_state, sampling_interval=None):
        self._sampling_rate = recording_utils.compute_rate(
            new_state, sampling_interval)

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if self._sampling_rate == 0:
            return 0

        out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * BYTES_PER_WORD
        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, out_spike_bytes)

    def get_extra_buffered_sdram(self):
        """
        Returns the maximum extra sdram where sampling is used.

        The assumption here is that the there has been a previous run which
        stopped just before the recording timestep.

        Then it is run for one timestep so a whole row of data must fit.
        This method returns the cost for a whole row
        minus the average returned by get_buffered_sdram_per_timestep

        :return:
        """
        rate = self._sampling_rate
        if rate <= 1:
            # No sampling so get_buffered_sdram_per_timestep was correct
            return 0
        data_size = self.N_BYTES_PER_NEURON * slice.n_atom
        return BYTES_PER_WORD / rate * (rate - 1)

    def get_dtcm_usage_in_bytes(self):
        if self._sampling_rate == 0:
            return 0
        return BYTES_PER_WORD / self._sampling_rate

    def get_n_cpu_cycles(self, n_neurons):
        if self._sampling_rate == 0:
            return 0
        return n_neurons * 4

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        return BYTES_PER_WORD

    def get_global_parameters(self, vertex_slice):
        return recording_utils.rate_parameter(self._sampling_rate)

    def get_spikes(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):

        spike_times = list()
        spike_ids = list()
        ms_per_tick = machine_time_step / 1000.0

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing_str = ""
        progress = ProgressBar(vertices,
                               "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            # Read the spikes
            n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
            n_bytes = n_words * BYTES_PER_WORD
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, data_missing = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
            record_raw = neuron_param_region_data_pointer.read_all()
            raw_data = (numpy.asarray(record_raw, dtype="uint8").
                        view(dtype="<i4")).reshape(
                [-1, n_words_with_timestamp])
            if len(raw_data) > 0:
                record_time = raw_data[:, 0] * float(ms_per_tick)
                spikes = raw_data[:, 1].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                time_indices, indices = numpy.where(bits == 1)
                times = record_time[time_indices].reshape((-1))
                indices = indices + vertex_slice.lo_atom
                spike_ids.extend(indices)
                spike_times.extend(times)

        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        if len(spike_ids) == 0:
            return numpy.zeros((0, 2), dtype="float")

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))]

    def get_spikes_sampling_interval(self):
        """
        Returns the current sampling interval for this variable
         :return: Sampling interval in micro seconds
        """
        return recording_utils.compute_interval(self._sampling_rate)
