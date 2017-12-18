from spinn_front_end_common.utilities import globals_variables
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import math
import numpy
import logging

logger = logging.getLogger(__name__)


class SpikeRecorder(object):

    def __init__(self):
        self._record = False

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if not self._record:
            return 0

        out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * 4
        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, out_spike_bytes)

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def get_spikes(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):

        spike_times = list()
        spike_ids = list()
        sampling_interval = self.get_spikes_sampling_interval()

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing_str = ""
        progress = ProgressBar(vertices,
                               "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            # Read the spikes
            n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
            n_bytes = n_words * 4
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
                split_record = numpy.array_split(raw_data, [1, 1], 1)

                record_time = raw_data[0][0] * float(sampling_interval)
                spikes = raw_data[0][1:].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                indices = numpy.where(bits == 1)[1]
                times = numpy.repeat(record_time, len(indices))
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
        return globals_variables.get_simulator().machine_time_step / 1000
