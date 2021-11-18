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

    def get_provenance_data(self, synapse_info):
        """ Get any provenance data
        :param SynapseInformation synapse_info
        """
        # pylint: disable=unused-argument
