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

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get any provenance data

        :param str pre_population_label: label of pre.
        :param str post_population_label: label of post.
        :return: the provenance data of the weight dependency
        :rtype:
            iterable(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """
        # pylint: disable=unused-argument
        return []

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
            self, spec, weight_scales, n_weight_terms):
        """ Write the parameters of the rule to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
        :param iterable(float) weight_scales:
        :param int n_weight_terms:
       """

    @abstractproperty
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule

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
