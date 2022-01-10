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

import math
import logging
import struct
import numpy
from pacman.model.resources.constant_sdram import ConstantSDRAM
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.common import recording_utils
from pacman.model.resources.variable_sdram import VariableSDRAM
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spynnaker.pyNN.data import SpynnakerDataView

logger = FormatAdapter(logging.getLogger(__name__))
_TWO_WORDS = struct.Struct("<II")


class MultiSpikeRecorder(object):
    __slots__ = [
        "__record"]

    def __init__(self):
        self.__record = False

    @property
    def record(self):
        """
        :rtype: bool
        """
        return self.__record

    @record.setter
    def record(self, record):
        self.__record = record

    def get_sdram_usage_in_bytes(self, n_neurons, spikes_per_timestep):
        """
        :rtype: ~pacman.model.resources.AbstractSDRAM
        """
        if not self.__record:
            return ConstantSDRAM(0)

        out_spike_bytes = (
            int(math.ceil(n_neurons / BITS_PER_WORD)) * BYTES_PER_WORD)
        return VariableSDRAM(0, (2 * BYTES_PER_WORD) + (
            out_spike_bytes * spikes_per_timestep))

    def get_dtcm_usage_in_bytes(self):
        """
        :rtype: int
        """
        if not self.__record:
            return 0
        return BYTES_PER_WORD

    def get_n_cpu_cycles(self, n_neurons):
        """
        :param int n_neurons:
        :rtype: int
        """
        if not self.__record:
            return 0
        return n_neurons * 4

    def get_spikes(
            self, label, buffer_manager, region, application_vertex):
        """
        :param str label:
        :param buffer_manager: the buffer manager object
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :param int region:
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :return: A numpy array of 2-element arrays of (neuron_id, time)
            ordered by time, one element per event
        :rtype: ~numpy.ndarray(tuple(int,int))
        """
        # pylint: disable=too-many-arguments
        spike_times = list()
        spike_ids = list()

        vertices = application_vertex.machine_vertices
        missing = []
        progress = ProgressBar(
            vertices, "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            vertex_slice = vertex.vertex_slice

            # Read the spikes from the buffer manager
            neuron_param_data, data_missing = \
                buffer_manager.get_data_by_placement(placement, region)
            if data_missing:
                missing.append(placement)
            self._process_spike_data(
                vertex_slice,
                int(math.ceil(vertex_slice.n_atoms / BITS_PER_WORD)),
                neuron_param_data, spike_ids, spike_times)

        if missing:
            logger.warning(
                "Population {} is missing spike data in region {} from the "
                "following cores: {}", label, region,
                recording_utils.make_missing_string(missing))

        if not spike_ids:
            return numpy.zeros((0, 2))

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]

    @staticmethod
    def _process_spike_data(
            vertex_slice, n_words, raw_data, spike_ids, spike_times):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int n_words:
        :param bytearray raw_data:
        :param list(~numpy.ndarray) spike_ids:
        :param list(~numpy.ndarray) spike_times:
        """
        # pylint: disable=too-many-arguments
        n_bytes_per_block = n_words * BYTES_PER_WORD
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
            times = numpy.repeat(
                [time * SpynnakerDataView().simulation_time_step_ms],
                len(indices))
            indices = indices + vertex_slice.lo_atom
            spike_ids.append(indices)
            spike_times.append(times)
