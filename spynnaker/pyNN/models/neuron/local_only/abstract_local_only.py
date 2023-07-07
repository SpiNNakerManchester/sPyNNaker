# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)


class AbstractLocalOnly(AbstractSynapseDynamics):
    """
    Processes synapses locally without the need for SDRAM.
    """

    @abstractmethod
    def get_parameters_usage_in_bytes(
            self, n_atoms, incoming_projections):
        """
        Get the size of the parameters in bytes.

        :param int n_atoms: The number of atoms in the vertex
        :param incoming_projections: The projections to get the size of
        :type incoming_projections:
            list(~spynnaker.pyNN.models.projection.Projection)
        :rtype: int
        """

    @abstractmethod
    def write_parameters(self, spec, region, machine_vertex, weight_scales):
        """
        Write the parameters to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            The machine vertex being targeted
        :param list(float) weight_scales: Scale factors to apply to the weights
        """

    @property
    def absolute_max_atoms_per_core(self):
        # A bit of an estimate for these local-only systems, which don't use
        # the master population table and so don't have the same limit
        return 2048

    @property
    @overrides(AbstractSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self):
        return True
