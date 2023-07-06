# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractSynapseDynamicsStructural(object, metaclass=AbstractBase):
    """
    Base class for synapse dynamics that structural plasticity understands.
    """

    @abstractmethod
    def get_structural_parameters_sdram_usage_in_bytes(
            self, incoming_projections, n_neurons):
        """
        Get the size of the structural parameters.

        .. note::
            At the Application level this will be an estimate.

        :param incoming_projections:
            The projections that target the vertex in question
        :type incoming_projections:
            list(~spynnaker.pyNN.models.projection.Projection)
        :param int n_neurons:
        :return: the size of the parameters, in bytes
        :rtype: int
        :raises PacmanInvalidParameterException:
            If the parameters make no sense.
        """

    @abstractmethod
    def write_structural_parameters(
            self, spec, region, weight_scales, app_vertex, vertex_slice,
            synaptic_matrices):
        """
        Write structural plasticity parameters.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param int region: region ID
        :param list(float) weight_scales: Weight scaling for each synapse type
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The target application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the target vertex to generate for
        :param SynapticMatrices synaptic_matrices:
            The synaptic matrices for this vertex
        """

    @abstractmethod
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info):
        """
        Set connections for structural plasticity.

        :param ~numpy.ndarray connections:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ProjectionApplicationEdge app_edge:
        :param SynapseInformation synapse_info:
        """

    @property
    @abstractmethod
    def f_rew(self):
        """
        The frequency of rewiring.

        :rtype: float
        """

    @property
    @abstractmethod
    def s_max(self):
        """
        The maximum number of synapses.

        :rtype: int
        """

    @property
    @abstractmethod
    def with_replacement(self):
        """
        Whether to allow replacement when creating synapses.

        :rtype: bool
        """

    @property
    @abstractmethod
    def seed(self):
        """
        The seed to control the randomness.
        """

    @property
    @abstractmethod
    def initial_weight(self):
        """
        The weight of a formed connection.

        :rtype: float
        """

    @property
    @abstractmethod
    def initial_delay(self):
        """
        The delay of a formed connection.

        :rtype: float or (float, float)
        """

    @property
    @abstractmethod
    def partner_selection(self):
        """
        The partner selection rule.

        :rtype: AbstractPartnerSelection
        """

    @property
    @abstractmethod
    def formation(self):
        """
        The formation rule.

        :rtype: AbstractFormation
        """

    @property
    @abstractmethod
    def elimination(self):
        """
        The elimination rule.

        :rtype: AbstractElimination
        """

    @abstractmethod
    def check_initial_delay(self, max_delay_ms):
        """
        Check that delays can be done without delay extensions.

        :param int max_delay_ms: The maximum delay supported, in milliseconds
        :raises Exception: if the delay is out of range
        """

    @abstractmethod
    def get_max_rewires_per_ts(self):
        """
        Get the max number of rewires per timestep.

        :rtype: int
        """
