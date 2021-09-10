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

from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import float_to_fixed
# Six words per synapse type
_SPACE_PER_SYNAPSE_TYPE = 6 * BYTES_PER_WORD


class WeightDependenceAdditiveTriplet(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    """ An triplet-based additive weight dependence STDP rule.
    """
    __slots__ = [
        "__a3_minus",
        "__a3_plus",
        "__w_max",
        "__w_min"]
    __PARAM_NAMES = ('w_min', 'w_max', 'A3_plus', 'A3_minus')

    default_parameters = {'w_min': 0.0, 'w_max': 1.0, 'A3_plus': 0.01,
                          'A3_minus': 0.01}

    # noinspection PyPep8Naming
    def __init__(
            self, w_min=default_parameters['w_min'],
            w_max=default_parameters['w_max'],
            A3_plus=default_parameters['A3_plus'],
            A3_minus=default_parameters['A3_minus']):
        """
        :param float w_min: :math:`w^{min}`
        :param float w_max: :math:`w^{max}`
        :param float A3_plus: :math:`A_3^+`
        :param float A3_minus: :math:`A_3^-`
        """
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max
        self.__a3_plus = A3_plus
        self.__a3_minus = A3_minus

    @property
    def w_min(self):
        """ :math:`w^{min}`

        :rtype: float
        """
        return self.__w_min

    @property
    def w_max(self):
        """ :math:`w^{max}`

        :rtype: float
        """
        return self.__w_max

    @property
    def A3_plus(self):
        """ :math:`A_3^+`

        :rtype: float
        """
        return self.__a3_plus

    @property
    def A3_minus(self):
        """ :math:`A_3^-`

        :rtype: float
        """
        return self.__a3_minus

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditiveTriplet):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus) and
            (self.__a3_plus == weight_dependence.A3_plus) and
            (self.__a3_minus == weight_dependence.A3_minus))

    @property
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """
        return "additive"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 2:
            raise NotImplementedError(
                "Additive weight dependence only supports one or two terms")
        return _SPACE_PER_SYNAPSE_TYPE * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec, weight_scales, n_weight_terms):

        # Loop through each synapse type
        for _ in weight_scales:

            # Scale the weights
            spec.write_value(
                data=float_to_fixed(self.__w_min), data_type=DataType.INT32)
            spec.write_value(
                data=float_to_fixed(self.__w_max), data_type=DataType.INT32)

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN
            #                /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=float_to_fixed(self.A_plus * self.__w_max),
                data_type=DataType.INT32)
            spec.write_value(
                data=float_to_fixed(self.A_minus * self.__w_max),
                data_type=DataType.INT32)
            spec.write_value(
                data=float_to_fixed(self.__a3_plus * self.__w_max),
                data_type=DataType.INT32)
            spec.write_value(
                data=float_to_fixed(self.__a3_minus * self.__w_max),
                data_type=DataType.INT32)

    @property
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """
        return self.__w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return self.__PARAM_NAMES
