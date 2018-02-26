from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter

from spynnaker.pyNN.models.common import recording_utils

import math
import numpy
import logging

logger = FormatAdapter(logging.getLogger(__name__))


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
        # pylint: disable=too-many-arguments, too-many-locals
        spike_times = list()
        spike_ids = list()
        ms_per_tick = float(machine_time_step) / 1000.0

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing = []
        progress = ProgressBar(
            vertices, "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            missing.extend(self._read_vertex_spikes(
                buffer_manager, region, ms_per_tick,
                placements.get_placement_of_vertex(vertex),
                graph_mapper.get_slice(vertex), spike_ids, spike_times))

        if missing:
            logger.warning(
                "Population {} is missing spike data in region {} from the "
                "following cores: {}", label, region,
                recording_utils.make_missing_string(missing))

        if not spike_ids:
            return numpy.zeros((0, 2), dtype="float")
        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]

    def _read_vertex_spikes(
            self, buffer_manager, region, ms_per_tick, placement, vertex_slice,
            spike_ids, spike_times):
        # pylint: disable=too-many-arguments, too-many-locals

        # Read the spikes from the buffer manager
        n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
        neuron_param_region, data_missing = \
            buffer_manager.get_data_for_vertex(placement, region)
        raw_data = numpy.asarray(
            neuron_param_region.read_all(), dtype="uint8").view(
                dtype="<i4").reshape([-1, n_words + 1])

        # If we have the data, build it into the form that PyNN expects
        if raw_data.size:
            split_record = numpy.array_split(raw_data, [1, 1], 1)
            record_time = split_record[0] * ms_per_tick
            spikes = split_record[2].byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                (-1, 32))).reshape((-1, n_words * 32))
            time_indices, indices = numpy.where(bits == 1)
            spike_ids.append(indices + vertex_slice.lo_atom)
            spike_times.append(record_time[time_indices].reshape((-1)))

        # If data was missing, ask for this placement to be reported as such
        return [placement] if data_missing else []
