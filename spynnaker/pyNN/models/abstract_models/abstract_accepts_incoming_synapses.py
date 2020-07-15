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

        :param str target: The name of the synapse
        :rtype: int
        """

    @abstractmethod
    def set_synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics of this vertex.

        :param AbstractSynapseDynamics synapse_dynamics:
        """

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by this vertex.

        :param int machine_time_step: microseconds
        :rtype: int
        """

    @abstractmethod
    def add_pre_run_connection_holder(
            self, connection_holder, projection_edge, synapse_information):
        """ Add a connection holder to the vertex to be filled in when the\
            connections are actually generated.

        :param ConnectionHolder connection_holder:
        :param ProjectionApplicationEdge projection_edge:
        :param SynapseInformation synapse_information:
        """

    @abstractmethod
    def get_connections_from_machine(
            self, transceiver, placement, edge, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements=None, monitor_api=None, monitor_cores=None,
            handle_time_out_configuration=True, fixed_routes=None,
            extra_monitor=None):
        # pylint: disable=too-many-arguments
        """ Get the connections from the machine post-run.

        :param ~spinnman.Transceiver transceiver:
        :param ~pacman.model.placements.Placement placement:
        :param ProjectionMachineEdge edge:
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        :param SynapseInformation synapse_information:
        :param int machine_time_step: microseconds
        :param bool using_extra_monitor_cores:
        :param placements:
        :type placements: None or ~pacman.model.placements.Placements
        :param monitor_api:
        :type monitor_api: None or \
            ~spinn_front_end_common.utility_models.DataSpeedUpPacketGatherMachineVertex
        :param monitor_placement:
        :type monitor_placement: None or ~pacman.model.placements.Placement
        :param monitor_cores:
        :type monitor_cores: None or \
            iterable(~spinn_front_end_common.utility_models.ExtraMonitorSupportMachineVertex)
        :param bool handle_time_out_configuration:
        :param fixed_routes:
        :type fixed_routes: None or \
            dict(tuple(int,int),~spinn_machine.FixedRouteEntry)
        """

    @abstractmethod
    def clear_connection_cache(self):
        """ Clear the connection data stored in the vertex so far.
        """

    @abstractmethod
    def get_in_coming_size(self):
        """ returns how many atoms are to be considered in incoming projections
        :return: returns the number of neurons to receive spikes from
        """

    @abstractmethod
    def gen_on_machine(self, vertex_slice):
        """returns a bool that states if the core has some synaptic data\
        that's generated on the machine via the synaptic expander
        :return: returns bool """
