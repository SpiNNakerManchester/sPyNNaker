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
from spynnaker.pyNN.models.common import recording_utils
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

    def get_spikes(self, label, region,
                   application_vertex, base_key_function):
        """ Get the recorded spikes from the object

        :param str label:
        :param int region:
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param base_key_function:
        :type base_key_function:
            callable(~pacman.model.graphs.machine.MachineVertex,int)
        :return: A numpy array of 2-element arrays of (neuron_id, time)
            ordered by time, one element per event
        :rtype: ~numpy.ndarray(tuple(int,int))
        """
        # pylint: disable=too-many-arguments
        results = list()
        missing = []
        vertices = application_vertex.machine_vertices
        progress = ProgressBar(vertices,
                               "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            vertex_slice = vertex.vertex_slice

            with NeoBufferDatabase() as db:
                results.extend(db.get_eieio_spikes(
                    placement.x, placement.y, placement.p, region,
                    SpynnakerDataView.get_simulation_time_step_ms(),
                    base_key_function(vertex), vertex_slice,
                    application_vertex.atoms_shape
                ))

        if missing:
            missing_str = recording_utils.make_missing_string(missing)
            logger.warning(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}", label, region, missing_str)
        if not results:
            return numpy.empty(shape=(0, 2))
        result = numpy.vstack(results)
        return result[numpy.lexsort((result[:, 1], result[:, 0]))]

    def write_spike_metadata(
            self, region, application_vertex, base_key_function):
        with NeoBufferDatabase() as db:
            vertices = application_vertex.machine_vertices
            for vertex in vertices:
                db.set_eieio_spikes_metadata(
                    vertex, "SPIKES", region, base_key_function(vertex),
                    application_vertex.atoms_shape)