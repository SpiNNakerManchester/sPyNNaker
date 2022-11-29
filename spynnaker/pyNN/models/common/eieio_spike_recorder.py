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
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase

logger = FormatAdapter(logging.getLogger(__name__))
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
        """
        :rtype: bool
        """
        return self.__record

    @record.setter
    def record(self, new_state):
        """ Old method assumed to be spikes """
        self.__record = new_state

    def set_recording(self, new_state, sampling_interval=None):
        """
        :param new_state: bool
        :param sampling_interval: not supported functionality
        """
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.__record = new_state

    def write_spike_metadata(
            self, region, application_vertex, base_key_function,
            n_colour_bits, first_id):
        """
         Write the metadata to retrieve spikes based on just the data

        :param int region: local region this vertex will write to
        :param ApplicationVertex application_vertex:
            vertex which will supply the data
        :param method base_key_function: Function to calculate the base key
        :param int n_colour_bits:
            The number of colour bits sent by this vertex.
        :param int first_id: The ID of the first member of the population.
        """
        with NeoBufferDatabase() as db:
            vertices = application_vertex.machine_vertices
            for vertex in vertices:
                vertex._update_virtual_key()
                db.write_eieio_spikes_metadata(
                    vertex, "spikes", region, base_key_function(vertex),
                    n_colour_bits,
                    SpynnakerDataView.get_simulation_time_step_ms(), first_id)
