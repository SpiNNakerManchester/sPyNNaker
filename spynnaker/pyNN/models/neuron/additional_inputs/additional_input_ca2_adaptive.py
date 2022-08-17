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
from .abstract_additional_input import AbstractAdditionalInput
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

I_ALPHA = "i_alpha"
I_CA2 = "i_ca2"
TAU_CA2 = "tau_ca2"
TIME_STEP = "time_step"


class AdditionalInputCa2Adaptive(AbstractAdditionalInput):
    __slots__ = [
        "__tau_ca2",
        "__i_ca2",
        "__i_alpha"]

    def __init__(self, tau_ca2, i_ca2, i_alpha):
        r"""
        :param tau_ca2: :math:`\tau_{\mathrm{Ca}^{+2}}`
        :type tau_ca2: float, iterable(float),
            ~pyNN.random.RandomDistribution or (mapping) function
        :param i_ca2: :math:`I_{\mathrm{Ca}^{+2}}`
        :type i_ca2: float, iterable(float),
            ~pyNN.random.RandomDistribution or (mapping) function
        :param i_alpha: :math:`I_{\alpha}`
        :type i_alpha: float, iterable(float),
            ~pyNN.random.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                 (DataType.S1615, TAU_CA2),
                 (DataType.S1615, I_CA2),
                 (DataType.S1615, I_ALPHA),
                 (DataType.S1615, TIME_STEP)])],
            {I_ALPHA: "nA", I_CA2: "nA", TAU_CA2: "ms"})
        self.__tau_ca2 = tau_ca2
        self.__i_ca2 = i_ca2
        self.__i_alpha = i_alpha

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_CA2] = self.__tau_ca2
        parameters[I_ALPHA] = self.__i_alpha
        parameters[TIME_STEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[I_CA2] = self.__i_ca2

    @property
    def tau_ca2(self):
        r""" Settable model parameter: :math:`\tau_{\mathrm{Ca}^{+2}}`

        :rtype: float
        """
        return self.__tau_ca2

    @property
    def i_ca2(self):
        r""" Settable model parameter: :math:`I_{\mathrm{Ca}^{+2}}`

        :rtype: float
        """
        return self.__i_ca2

    @property
    def i_alpha(self):
        r""" Settable model parameter: :math:`I_{\alpha}`

        :rtype: float
        """
        return self.__i_alpha
