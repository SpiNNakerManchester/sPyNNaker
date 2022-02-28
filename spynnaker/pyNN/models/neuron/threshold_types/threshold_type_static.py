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
from .abstract_threshold_type import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct

V_THRESH = "v_thresh"


class ThresholdTypeStatic(AbstractThresholdType):
    """ A threshold that is a static value.
    """
    __slots__ = ["__v_thresh"]

    def __init__(self, v_thresh):
        """
        :param v_thresh: :math:`V_{thresh}`
        :type v_thresh:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__(
            [Struct([(DataType.S1615, V_THRESH)])],
            {V_THRESH: "mV"})
        self.__v_thresh = v_thresh

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # Just a comparison, but 2 just in case!
        return 2 * n_neurons

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_THRESH] = self.__v_thresh

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @property
    def v_thresh(self):
        """
        :math:`V_{thresh}`
        """
        return self.__v_thresh
