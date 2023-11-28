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
from __future__ import annotations
from numpy import floating
from numpy.typing import NDArray
from typing import Iterable, TYPE_CHECKING
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataSpecificationGenerator
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)
from spynnaker.pyNN.types import Weight_Delay_In_Types
if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neuron import (
        PopulationMachineLocalOnlyCombinedVertex)


class AbstractLocalOnly(AbstractSynapseDynamics):
    """
    Processes synapses locally without the need for SDRAM.
    """

    def __init__(self, delay: Weight_Delay_In_Types):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        # We don't have a weight here, it is in the connector
        super().__init__(delay=delay, weight=None)

    @abstractmethod
    def get_parameters_usage_in_bytes(
            self, n_atoms: int,
            incoming_projections: Iterable[Projection]) -> int:
        """
        Get the size of the parameters in bytes.

        :param int n_atoms: The number of atoms in the vertex
        :param incoming_projections: The projections to get the size of
        :type incoming_projections:
            list(~spynnaker.pyNN.models.projection.Projection)
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def write_parameters(
            self, spec: DataSpecificationGenerator, region: int,
            machine_vertex: PopulationMachineLocalOnlyCombinedVertex,
            weight_scales: NDArray[floating]) -> None:
        """
        Write the parameters to the data specification for a vertex.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            The machine vertex being targeted
        :param list(float) weight_scales: Scale factors to apply to the weights
        """
        raise NotImplementedError

    @property
    def absolute_max_atoms_per_core(self) -> int:
        """
        The absolute maximum number of atoms per core.

        .. note::
            This is *not* constrained by the usual limits of the master
            population table.

        :rtype: int
        """
        # A bit of an estimate for these local-only systems, which don't use
        # the master population table and so don't have the same limit
        return 2048

    @property
    @overrides(AbstractSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        return True
