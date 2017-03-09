from spinn_machine.utilities.progress_bar import ProgressBar

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
        ms_per_tick = machine_time_step / 1000.0

        vertices = \
            graph_mapper.get_machine_vertices(application_vertex)

        missing_str = ""

        progress_bar = ProgressBar(len(vertices),
                                   "Getting spikes for {}".format(label))
        for vertex in vertices:

            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            x = placement.x
            y = placement.y
            p = placement.p
            lo_atom = vertex_slice.lo_atom

            # Read the spikes
            n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
            n_bytes = n_words * 4
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, data_missing = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(x, y, p)
            record_raw = neuron_param_region_data_pointer.read_all()
            raw_data = (numpy.asarray(record_raw, dtype="uint8").
                        view(dtype="<i4")).reshape(
                [-1, n_words_with_timestamp])
            if len(raw_data) > 0:
                split_record = numpy.array_split(raw_data, [1, 1], 1)
                record_time = split_record[0] * float(ms_per_tick)
                spikes = split_record[2].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                time_indices, indices = numpy.where(bits == 1)
                times = record_time[time_indices].reshape((-1))
                indices = indices + lo_atom
                spike_ids.append(indices)
                spike_times.append(times)
                progress_bar.update()

        progress_bar.end()
        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        if len(spike_ids) == 0:
            return numpy.zeros((0, 2), dtype="float")
        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]
