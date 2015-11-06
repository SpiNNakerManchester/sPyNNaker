from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.utilities import constants

import math
import numpy
import logging

logger = logging.getLogger(__name__)


class SpikeRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
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

        # size computed without buffering out technique
        # out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * 4
        # return recording_utils.get_recording_region_size_in_bytes(
        #    n_machine_time_steps, out_spike_bytes)

        # size computed for buffering out technique
        return constants.SPIKE_BUFFER_SIZE_BUFFERING_OUT

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def get_spikes(self, label, buffer_manager, region, state_region,
                   placements, graph_mapper, partitionable_vertex):

        spike_times = list()
        spike_ids = list()
        ms_per_tick = self._machine_time_step / 1000.0

        subvertices = \
            graph_mapper.get_subvertices_from_vertex(partitionable_vertex)

        missing = list()

        progress_bar = ProgressBar(len(subvertices),
                                   "Getting spikes for {}".format(label))
        for subvertex in subvertices:

            placement = placements.get_placement_of_subvertex(subvertex)
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)

            x = placement.x
            y = placement.y
            p = placement.p
            lo_atom = subvertex_slice.lo_atom

            # Read the spikes
            n_words = int(math.ceil(subvertex_slice.n_atoms / 32.0))
            n_bytes = n_words * 4
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_processor = \
                buffer_manager.get_data_for_vertex(
                    x, y, p, region, state_region)
            if missing_processor is not None:
                missing.append(missing_processor)
            record_raw = neuron_param_region_data_pointer.read_all()
            raw_data = (numpy.asarray(record_raw, dtype="uint8").
                        view(dtype="<i4")).reshape(
                [-1, n_words_with_timestamp])
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
        for i in missing:
            logger.info("Missing information in chip ({0:d},{1:d}), core {2:d},"
                        " population {3:s}, for region {4:d}".format(
                            i[0], i[1], i[2], label, i[3]))

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]
