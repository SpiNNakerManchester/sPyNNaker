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


class AbstractWeightDependence(object, metaclass=AbstractBase):
    __slots__ = ()

    @abstractmethod
    def get_parameter_names(self):
        """ Returns the parameter names

        :rtype: iterable(str)
        """

    @abstractmethod
    def is_same_as(self, weight_dependence):
        """ Determine if this weight dependence is the same as another

        :param AbstractWeightDependence weight_dependence:
        :rtype: bool
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        """ Get the amount of SDRAM used by the parameters of this rule

        :param int n_synapse_types:
        :param int n_weight_terms:
        :rtype: int
        """

    @abstractmethod
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales,
            n_weight_terms):
        """ Write the parameters of the rule to the spec

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
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """
