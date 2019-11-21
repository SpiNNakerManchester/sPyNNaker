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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractWeightDependence(object):
    __slots__ = ()

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get any provenance data

        :param pre_population_label: label of pre.
        :type pre_population_label: str
        :param post_population_label: label of post.
        :type post_population_label: str
        :return: the provenance data of the weight dependency
        :rtype: list
        """
        # pylint: disable=unused-argument
        return list()

    @abstractmethod
    def get_parameter_names(self):
        """ Returns the parameter names

        :rtype: iterable(str)
        """

    @abstractmethod
    def is_same_as(self, weight_dependence):
        """ Determine if this weight dependence is the same as another

        :param weight_dependence:
        :type weight_dependence: AbstractWeightDependence
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

        :param n_synapse_types:
        :type n_synapse_types: int
        :param n_weight_terms:
        :type n_weight_terms: int
        :rtype: int
        """

    @abstractmethod
    def write_parameters(
            self, spec, machine_time_step, weight_scales, n_weight_terms):
        """ Write the parameters of the rule to the spec

        :param spec:
        :type spec: ~data_specification.DataSpecificationGenerator
        :param machine_time_step: (unused?)
        :type machine_time_step: int
        :param weight_scales:
        :type weight_scales: iterable(float)
        :param n_weight_terms:
        :type n_weight_terms: int
       """

    @abstractproperty
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """
