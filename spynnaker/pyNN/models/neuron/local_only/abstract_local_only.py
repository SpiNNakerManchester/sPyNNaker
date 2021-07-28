# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)


class AbstractLocalOnly(AbstractSynapseDynamics):
    """ Processes synapses locally without the need for SDRAM.
    """

    @abstractmethod
    def get_parameters_usage_in_bytes(self, incoming_projections):
        """ Get the size of the parameters in bytes

        :param list(~spynnaker.pyNN.models.projection.Projection)\
                incoming_projections:
            The projections to get the size of
        :rtype: int
        """

    @abstractmethod
    def write_parameters(
            self, spec, region, routing_info, incoming_projections,
            machine_vertex, weight_scales):
        """ Write the parameters to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param RoutingInfo routing_info: Information about routing keys
        :param list(~spynnaker.pyNN.models.projection.Projection) \
                incoming_projections:
            List of projections that target this core
        :param MachineVertex machine_vertex: The machine vertex being targeted
        :param list(float) weight_scales: Scale factors to apply to the weights
        """
