from pacman.model.decorators import overrides
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import math
import numpy
import logging
import struct

logger = logging.getLogger(__name__)
_TWO_WORDS = struct.Struct("<II")


class MultiSpikeRecorder(object):

    def __init__(self):
        self._record = False

    @property
    def record(self):
        return self._record

    def set_recording(self, new_state, sampling_interval=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported "
                           "so being ignored")
        self._record = new_state

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

    def get_spikes(
            self, label, buffer_manager, region,
            placements, graph_mapper, application_vertex, machine_time_step):

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

            x = placement.x
            y = placement.y
            p = placement.p
            lo_atom = vertex_slice.lo_atom

            # Read the spikes
            n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
            n_bytes_per_block = n_words * 4

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, data_missing = \
                buffer_manager.get_data_for_vertex(placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(x, y, p)
            raw_data = neuron_param_region_data_pointer.read_all()
            offset = 0
            while offset < len(raw_data):
                time, n_blocks = _TWO_WORDS.unpack_from(raw_data, offset)
                offset += _TWO_WORDS.size
                spike_data = numpy.frombuffer(
                    raw_data, dtype="uint8",
                    count=n_bytes_per_block * n_blocks, offset=offset)
                offset += n_bytes_per_block * n_blocks
                spikes = spike_data.view("<i4").byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes_per_block * 8))
                indices = numpy.nonzero(bits)[1]
                times = numpy.repeat([time * ms_per_tick], len(indices))
                indices = indices + lo_atom
                spike_ids.append(indices)
                spike_times.append(times)

        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        if len(spike_ids) > 0:
            spike_ids = numpy.hstack(spike_ids)
            spike_times = numpy.hstack(spike_times)
            result = numpy.dstack((spike_ids, spike_times))[0]
            return result[numpy.lexsort((spike_times, spike_ids))]

        return numpy.zeros((0, 2))
