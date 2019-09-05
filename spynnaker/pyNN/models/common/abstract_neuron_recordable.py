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
class AbstractNeuronRecordable(object):
    """ Indicates that a variable (e.g., membrane voltage) can be recorded\
        from this object
    """

    __slots__ = ()

    @abstractmethod
    def get_recordable_variables(self):
        """ Returns a list of the variables this models is expected to collect
        """

    @abstractmethod
    def is_recording(self, variable):
        """ Determines if variable is being recorded

        :return: True if variable are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording(
            self, variable, default_machine_time_step, new_state=True,
            sampling_interval=None, indexes=None):
        """ Sets variable to being recorded
        """

    @abstractmethod
    def get_machine_vertices_for(self, variable, graph_mapper):
        """ gives the machine vertices for a given variable from a given app \
        vertex

        :param variable: the variable to get
        :param graph_mapper:  the mapping between graphs
        :return: iterable of machine vertex
        """

    @abstractmethod
    def clear_recording(self, variable, buffer_manager, placements,
                        graph_mapper):
        """ Clear the recorded data from the object

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :rtype: None
        """

    @abstractmethod
    def get_data(
            self, variable, run_time, placements, graph_mapper,
            buffer_manager, local_time_period_map):
        """ Get the recorded data

        :param variable: the variable name to get data for
        :param run_time: how long the simulation ran for this step /
        (not total runtime)
        :param placements: placements
        :param graph_mapper: mapping between app and machine graphs
        :param buffer_manager: buffer manager
        :param local_time_period_map: map between machine vertex and time /
        period
        :return: numpy array of the data
        """
        # pylint: disable=too-many-arguments

    @abstractmethod
    def get_neuron_sampling_interval(
            self, variable, graph_mapper, local_time_period_map):
        """ Returns the current sampling interval for this variable

        :param variable: PyNN name of the variable
        :param graph_mapper: the map between app graph and machine graph
        :param local_time_period_map: \
            the map of machine vertex to local time period
        :return: Sampling interval in micro seconds
        """

    @abstractmethod
    def get_expected_n_rows(
            self, run_time, local_time_period_map, sampling_rate, vertex):
        """ Returns the number of expected rows for a given runtime
        
        :param run_time: 
        :param local_time_period_map: 
        :param sampling_rate: 
        :param vertex:
        :return: 
        """