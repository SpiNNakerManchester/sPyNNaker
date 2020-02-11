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
class AbstractAcceptsIncomingSynapses(object):
    """ Indicates an object that can be a post-vertex in a PyNN projection.
    """
    __slots__ = ()

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the ID of a synapse given the name.

        :param target: The name of the synapse
        :type target: str
        :rtype: int
        """

    @abstractmethod
    def set_synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics of this vertex.
        """

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by this vertex.
        """

    @abstractmethod
    def add_pre_run_connection_holder(
            self, connection_holder, projection_edge, synapse_information):
        """ Add a connection holder to the vertex to be filled in when the\
            connections are actually generated.
        """

    @abstractmethod
    def get_connections_from_machine(
            self, transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements=None, monitor_api=None, monitor_cores=None,
            handle_time_out_configuration=True, fixed_routes=None,
            extra_monitor=None):
        # pylint: disable=too-many-arguments
        """ Get the connections from the machine post-run.
        """

    @abstractmethod
    def clear_connection_cache(self):
        """ Clear the connection data stored in the vertex so far.
        """
