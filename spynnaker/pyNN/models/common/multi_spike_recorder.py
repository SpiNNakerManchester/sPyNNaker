import math
import logging
import struct
import numpy
from pacman.model.resources.constant_sdram import ConstantSDRAM
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.common import recording_utils
from pacman.model.resources.variable_sdram import VariableSDRAM

logger = FormatAdapter(logging.getLogger(__name__))
_TWO_WORDS = struct.Struct("<II")


class MultiSpikeRecorder(object):
    __slots__ = [
        "__record"]

    def __init__(self):
        self.__record = False

    @property
    def record(self):
        return self.__record

    @record.setter
    def record(self, record):
        self.__record = record

    def get_sdram_usage_in_bytes(self, n_neurons, spikes_per_timestep):
        if not self.__record:
            return ConstantSDRAM(0)

        out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * 4
        return VariableSDRAM(0, 8 + (out_spike_bytes * spikes_per_timestep))

    def get_dtcm_usage_in_bytes(self):
        if not self.__record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self.__record:
            return 0
        return n_neurons * 4

    def get_spikes(
            self, label, buffer_manager, region,
            placements, graph_mapper, application_vertex, machine_time_step):
        # pylint: disable=too-many-arguments
        spike_times = list()
        spike_ids = list()
        ms_per_tick = machine_time_step / 1000.0

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing = []
        progress = ProgressBar(
            vertices, "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            # Read the spikes from the buffer manager
            neuron_param_data, data_missing = \
                buffer_manager.get_data_by_placement(placement, region)
            if data_missing:
                missing.append(placement)
            self._process_spike_data(
                vertex_slice, ms_per_tick,
                int(math.ceil(vertex_slice.n_atoms / 32.0)),
                neuron_param_data, spike_ids, spike_times)

        if missing:
            logger.warning(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}", label, region,
                recording_utils.make_missing_string(missing))

        if not spike_ids:
            return numpy.zeros((0, 2))

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]

    @staticmethod
    def _process_spike_data(
            vertex_slice, ms_per_tick, n_words, raw_data, spike_ids,
            spike_times):
        # pylint: disable=too-many-arguments
        n_bytes_per_block = n_words * 4
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
            indices = indices + vertex_slice.lo_atom
            spike_ids.append(indices)
            spike_times.append(times)
