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
        :param post_population_label: label of post.
        :return: the provenance data of the weight dependency
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
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        """ Get the amount of SDRAM used by the parameters of this rule
        """

    @abstractmethod
    def write_parameters(
            self, spec, machine_time_step, weight_scales, n_weight_terms):
        """ Write the parameters of the rule to the spec
        """

    @abstractproperty
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule
        """
