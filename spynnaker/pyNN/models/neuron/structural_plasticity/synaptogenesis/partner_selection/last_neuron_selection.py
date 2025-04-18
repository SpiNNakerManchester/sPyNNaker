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

from typing import Iterable
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataSpecificationBase
from .abstract_partner_selection import AbstractPartnerSelection


class LastNeuronSelection(AbstractPartnerSelection):
    """
    Partner selection that picks a random source neuron from the neurons
    that spiked in the last timestep.
    """

    __slots__ = ("__spike_buffer_size", )

    def __init__(self, spike_buffer_size: int = 64):
        """
        :param spike_buffer_size: The size of the buffer for holding spikes
        """
        self.__spike_buffer_size = spike_buffer_size

    @property
    @overrides(AbstractPartnerSelection.vertex_executable_suffix)
    def vertex_executable_suffix(self) -> str:
        return "_last_neuron"

    @overrides(AbstractPartnerSelection.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        return 4

    @overrides(AbstractPartnerSelection.write_parameters)
    def write_parameters(self, spec: DataSpecificationBase) -> None:
        spec.write_value(self.__spike_buffer_size)

    @overrides(AbstractPartnerSelection.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        yield "spike_buffer_size"
