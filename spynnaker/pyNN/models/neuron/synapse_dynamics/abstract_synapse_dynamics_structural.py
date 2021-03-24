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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)


class AbstractSynapseDynamicsStructural(object, metaclass=AbstractBase):

    @abstractmethod
    def get_structural_parameters_sdram_usage_in_bytes(
            self, graph, vertex, n_neurons):
        """ Get the size of the structural parameters

        Note: At the Application level this will be an estimate.

        :param graph: Graph at same level as vertex.
        :type graph: ~pacman.model.graphs.application.ApplicationGraph or
            ~pacman.model.graphs.machine.MachineGraph
        :param vertex: Vertex at the same level as the graph
        :type vertex: ~pacman.model.graphs.application.ApplicationVertex or
            ~pacman.model.graphs.machine.MachineVertex
        :param int n_neurons:
        :return: the size of the parameters, in bytes
        :rtype: int
        :raises PacmanInvalidParameterException:
        """

    @abstractmethod
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            machine_graph, machine_vertex, routing_info, synaptic_matrices):
        """ Write structural plasticity parameters

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param int region: region ID
        :param float machine_time_step: The simulation time step
        :param list(float) weight_scales: Weight scaling for each synapse type
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The machine graph
        :param AbstractPopulationVertex machine_vertex:
            The machine vertex
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            Routing information for all edges
        :param SynapticMatrices synaptic_matrices:
            The synaptic matrices for this vertex
        """

    @abstractmethod
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        """ Set connections for structural plasticity

        :param ~numpy.ndarray connections:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ProjectionApplicationEdge app_edge:
        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.machine.MachineEdge machine_edge:
        """

    @abstractproperty
    def f_rew(self):
        """ The frequency of rewiring

        :rtype: float
        """

    @abstractproperty
    def s_max(self):
        """ The maximum number of synapses

        :rtype: int
        """

    @abstractproperty
    def with_replacement(self):
        """ Whether to allow replacement when creating synapses

        :rtype: bool
        """

    @abstractproperty
    def seed(self):
        """ The seed to control the randomness
        """

    @abstractproperty
    def initial_weight(self):
        """ The weight of a formed connection

        :rtype: float
        """

    @abstractproperty
    def initial_delay(self):
        """ The delay of a formed connection

        :rtype: float or (float, float)
        """

    @abstractproperty
    def partner_selection(self):
        """ The partner selection rule

        :rtype: AbstractPartnerSelection
        """

    @abstractproperty
    def formation(self):
        """ The formation rule

        :rtype: AbstractFormation
        """

    @abstractproperty
    def elimination(self):
        """ The elimination rule

        :rtype: AbstractElimination
        """

    @abstractmethod
    def check_initial_delay(self, max_delay_ms):
        """ Check that delays can be done without delay extensions

        :param int max_delay_ms: The maximum delay supported, in milliseconds
        :raises Exception: if the delay is out of range
        """
