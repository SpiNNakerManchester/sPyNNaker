from spinn_machine.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.models.common import recording_utils

import math
import numpy
import logging
import struct

logger = logging.getLogger(__name__)


class MultiSpikeRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record = False

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def get_sdram_usage_in_bytes(
            self, n_neurons, spikes_per_timestep, n_machine_time_steps):
        if not self._record:
            return 0

        out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * 4
        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, out_spike_bytes * spikes_per_timestep)

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

        missing_str = ""

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
            n_bytes_per_block = n_words * 4

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, data_missing = \
                buffer_manager.get_data_for_vertex(
                    placement, region, state_region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(x, y, p)
            raw_data = neuron_param_region_data_pointer.read_all()
            offset = 0
            while offset < len(raw_data):
                ((time, n_blocks), offset) = (
                    struct.unpack_from("<II", raw_data, offset), offset + 8)
                (spike_data, offset) = (numpy.frombuffer(
                    raw_data, dtype="uint8",
                    count=n_bytes_per_block * n_blocks, offset=offset),
                    offset + (n_bytes_per_block * n_blocks))
                spikes = spike_data.view("<i4").byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes_per_block * 8))
                indices = numpy.nonzero(bits)[1]
                times = numpy.repeat([time * ms_per_tick], len(indices))
                indices = indices + lo_atom
                spike_ids.append(indices)
                spike_times.append(times)
            progress_bar.update()

        progress_bar.end()
        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]
