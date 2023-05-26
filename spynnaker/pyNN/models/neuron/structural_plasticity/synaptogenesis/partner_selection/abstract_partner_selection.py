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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractHasParameterNames)


class AbstractPartnerSelection(
        AbstractHasParameterNames, metaclass=AbstractBase):
    """
    A partner selection rule.
    """

    __slots__ = ()

    @abstractproperty
    def vertex_executable_suffix(self):
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self):
        """
        Get the amount of SDRAM used by the parameters of this rule.

        :rtype: str
        """

    @abstractmethod
    def write_parameters(self, spec):
        """
        Write the parameters of the rule to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
        """
