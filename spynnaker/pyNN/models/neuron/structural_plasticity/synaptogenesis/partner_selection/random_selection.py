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

from spinn_utilities.overrides import overrides
from .abstract_partner_selection import AbstractPartnerSelection


class RandomSelection(AbstractPartnerSelection):
    """
    Partner selection that picks a random source neuron from all sources.
    """

    __slots__ = ()

    @property
    @overrides(AbstractPartnerSelection.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_random"

    @overrides(AbstractPartnerSelection.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 0

    @overrides(AbstractPartnerSelection.write_parameters)
    def write_parameters(self, spec):
        pass

    @overrides(AbstractPartnerSelection.get_parameter_names)
    def get_parameter_names(self):
        return ()
