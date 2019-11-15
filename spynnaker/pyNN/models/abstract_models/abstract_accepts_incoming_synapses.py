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

        :param synapse_dynamics:
        :type synapse_dynamics: AbstractSynapseDynamics
        """

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by this vertex.

        :param machine_time_step: microseconds
        :type machine_time_step: int
        :rtype: int
        """

    @abstractmethod
    def add_pre_run_connection_holder(
            self, connection_holder, projection_edge, synapse_information):
        """ Add a connection holder to the vertex to be filled in when the\
            connections are actually generated.

        :param connection_holder:
        :type connection_holder: ConnectionHolder
        :param projection_edge:
        :type projection_edge: ProjectionApplicationEdge
        :param synapse_information:
        :type synapse_information: SynapseInformation
        """

    @abstractmethod
    def get_connections_from_machine(
            self, transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements=None, monitor_api=None, monitor_placement=None,
            monitor_cores=None, handle_time_out_configuration=True,
            fixed_routes=None):
        # pylint: disable=too-many-arguments
        """ Get the connections from the machine post-run.

        :param transceiver:
        :type transceiver: ~spinnman.Transceiver
        :param placement:
        :type placement: ~pacman.model.placements.Placement
        :param edge:
        :type edge: ProjectionMachineEdge
        :param routing_infos:
        :type routing_infos: ~pacman.model.routing_info.RoutingInfo
        :param synapse_information:
        :type synapse_information: SynapseInformation
        :param machine_time_step: microseconds
        :type machine_time_step: int
        :param using_extra_monitor_cores:
        :type using_extra_monitor_cores: bool
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
        :param handle_time_out_configuration:
        :type handle_time_out_configuration: bool
        :param fixed_routes:
        :type fixed_routes: None or \
            dict(tuple(int,int),~spinn_machine.FixedRouteEntry)
        """

    @abstractmethod
    def clear_connection_cache(self):
        """ Clear the connection data stored in the vertex so far.
        """
