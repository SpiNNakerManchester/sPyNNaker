# Copyright (c) 2015 The University of Manchester
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


class AbstractWeightDependence(object, metaclass=AbstractBase):
    __slots__ = ()

    @abstractmethod
    def get_parameter_names(self):
        """
        Returns the parameter names.

        :rtype: iterable(str)
        """

    @abstractmethod
    def is_same_as(self, weight_dependence):
        """
        Determine if this weight dependence is the same as another.

        :param AbstractWeightDependence weight_dependence:
        :rtype: bool
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        """
        Get the amount of SDRAM used by the parameters of this rule.

        :param int n_synapse_types:
        :param int n_weight_terms:
        :rtype: int
        """

    @abstractmethod
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales,
            n_weight_terms):
        """
        Write the parameters of the rule to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
        :param int n_weight_terms: The number of terms used by the synapse rule
       """

    @abstractproperty
    def weight_maximum(self):
        """
        The maximum weight that will ever be set in a synapse as a result
        of this rule.

        :rtype: float
        """

    @abstractproperty
    def weight_minimum(self):
        """ The minimum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """

    @abstractmethod
    def weight_change_minimum(self, min_delta):
        """ The minimum non-zero change in weight that will occur

        :param list min_delta: The minimum delta values from the timing rules
        :rtype: float
        """
