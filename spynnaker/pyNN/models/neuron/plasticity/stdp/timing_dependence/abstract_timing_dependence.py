# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractTimingDependence(object, metaclass=AbstractBase):

    __slots__ = ()

    @abstractmethod
    def is_same_as(self, timing_dependence):
        """ Determine if this timing dependence is the same as another

        :param AbstractTimingDependence timing_dependence:
        :rtype: bool
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """

    @abstractproperty
    def pre_trace_n_bytes(self):
        """ The number of bytes used by the pre-trace of the rule per neuron

        :rtype: int
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self):
        """ Get the amount of SDRAM used by the parameters of this rule

        :rtype: int
        """

    @abstractproperty
    def n_weight_terms(self):
        """ The number of weight terms expected by this timing rule

        :rtype: int
        """

    @abstractmethod
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales):
        """ Write the parameters of the rule to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
        """

    @abstractproperty
    def synaptic_structure(self):
        """ Get the synaptic structure of the plastic part of the rows

        :rtype: AbstractSynapseStructure
        """

    @abstractmethod
    def get_parameter_names(self):
        """ Return the names of the parameters supported by this timing\
            dependency model.

        :rtype: iterable(str)
        """
