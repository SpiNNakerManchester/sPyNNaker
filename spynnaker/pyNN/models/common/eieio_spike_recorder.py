# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import struct
import numpy
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from spinnman.messages.eieio.data_messages import EIEIODataHeader
from spynnaker.pyNN.models.common import recording_utils
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

logger = FormatAdapter(logging.getLogger(__name__))
_ONE_WORD = struct.Struct("<I")
_TWO_WORDS = struct.Struct("<II")


class EIEIOSpikeRecorder(object):
    """ Records spikes using EIEIO format
    """
    __slots__ = [
        "__record"]

    def __init__(self):
        self.__record = False

    @property
    def record(self):
        return self.__record

    @record.setter
    def record(self, new_state):
        """ Old method assumed to be spikes """
        self.__record = new_state

    def set_recording(self, new_state, sampling_interval=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.__record = new_state

    def get_dtcm_usage_in_bytes(self):
        if not self.__record:
            return 0
        return BYTES_PER_WORD

    def get_n_cpu_cycles(self, n_neurons):
        if not self.__record:
            return 0
        return n_neurons * 4

    def get_spikes(self, label, buffer_manager, region,
                   placements, graph_mapper, application_vertex,
                   base_key_function, machine_time_step):
        # pylint: disable=too-many-arguments
        results = list()
        missing = []
        ms_per_tick = machine_time_step / 1000.0
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(vertices,
                               "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            # Read the spikes
            n_buffer_times = 0
            if vertex.send_buffer_times is not None:
                for i in vertex.send_buffer_times:
                    if hasattr(i, "__len__"):
                        n_buffer_times += len(i)
                    else:
                        # assuming this must be a single integer
                        n_buffer_times += 1

            if (n_buffer_times > 0):
                raw_spike_data, data_missing = \
                    buffer_manager.get_data_by_placement(placement, region)
                if data_missing:
                    missing.append(placement)
                self._process_spike_data(
                    vertex_slice, raw_spike_data, ms_per_tick,
                    base_key_function(vertex), results)

        if missing:
            missing_str = recording_utils.make_missing_string(missing)
            logger.warning(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}", label, region, missing_str)
        if not results:
            return numpy.empty(shape=(0, 2))
        result = numpy.vstack(results)
        return result[numpy.lexsort((result[:, 1], result[:, 0]))]

    @staticmethod
    def _process_spike_data(
            vertex_slice, spike_data, ms_per_tick, base_key, results):
        number_of_bytes_written = len(spike_data)
        offset = 0
        while offset < number_of_bytes_written:
            length, time = _TWO_WORDS.unpack_from(spike_data, offset)
            time *= ms_per_tick
            data_offset = offset + 2 * BYTES_PER_WORD

            eieio_header = EIEIODataHeader.from_bytestring(
                spike_data, data_offset)
            if eieio_header.eieio_type.payload_bytes > 0:
                raise Exception("Can only read spikes as keys")

            data_offset += eieio_header.size
            timestamps = numpy.repeat([time], eieio_header.count)
            key_bytes = eieio_header.eieio_type.key_bytes
            keys = numpy.frombuffer(
                spike_data, dtype="<u{}".format(key_bytes),
                count=eieio_header.count, offset=data_offset)

            neuron_ids = (keys - base_key) + vertex_slice.lo_atom
            offset += length + 2 * BYTES_PER_WORD
            results.append(numpy.dstack((neuron_ids, timestamps))[0])
