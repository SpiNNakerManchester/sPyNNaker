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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSpikeRecordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_spikes(self):
        """ Determine if spikes are being recorded

        :return: True if spikes are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_spikes(
            self, default_machine_time_step, new_state=True,
            sampling_interval=None, indexes=None):
        """ Set spikes to being recorded. \
            If new_state is false all other parameters are ignored.

        :param default_machine_time_step: the simulation machine time step
        :type default_machine_time_step: int
        :param new_state: Set if the spikes are recording or not
        :type new_state: bool
        :param sampling_interval: The interval at which spikes are recorded.\
            Must be a whole multiple of the timestep
            None will be taken as the timestep
        :param indexes: The indexes of the neurons that will record spikes.
            If None the assumption is all neurons are recording
        """

    @abstractmethod
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        """ Clear the recorded data from the object

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :rtype: None
        """

    @abstractmethod
    def get_spikes(
            self, placements, graph_mapper, buffer_manager,
            local_timer_period_map):
        """ Get the recorded spikes from the object

        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :param buffer_manager: the buffer manager object
        :param local_timer_period_map: the time step of the verts
        :return: A numpy array of 2-element arrays of (neuron_id, time)\
            ordered by time
        """

    @abstractmethod
    def get_spike_machine_vertices(self, graph_mapper):
        """ get the machine vertices from the app vertex 
        
        :param graph_mapper: the graph mapper
        :return: iterable of machine vertices
        """

    @abstractmethod
    def get_spikes_sampling_interval(
            self, graph_mapper, local_time_period_map):
        """ Return the current sampling interval for spikes

        :param graph_mapper: map between app graph and machine graph
        :param local_time_period_map
        :return: Sampling interval in micro seconds
        """
