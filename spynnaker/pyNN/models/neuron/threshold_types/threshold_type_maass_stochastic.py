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

DU_TH = "du_th"
TAU_TH = "tau_th"
V_THRESH = "v_thresh"

UNITS = {
    DU_TH: "mV",
    TAU_TH: "ms",
    V_THRESH: "mV"
}


class ThresholdTypeMaassStochastic(AbstractThresholdType):
    """ A stochastic threshold.

    Habenschuss S, Jonke Z, Maass W. Stochastic computations in cortical \
    microcircuit models. *PLoS Computational Biology.* 2013;9(11):e1003311. \
    `doi:10.1371/journal.pcbi.1003311 \
    <https://doi.org/10.1371/journal.pcbi.1003311>`_
    """
    __slots__ = [
        "__du_th",
        "__tau_th",
        "__v_thresh"]

    def __init__(self, du_th, tau_th, v_thresh):
        r"""
        :param du_th: :math:`du_{thresh}`
        :type du_th: float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param tau_th: :math:`\tau_{thresh}`
        :type tau_th: float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param v_thresh: :math:`V_{thresh}`
        :type v_thresh:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__([
            DataType.S1615,   # 1 / du_th
            DataType.S1615,   # 1 / tau_th
            DataType.S1615,   # v_thresh
            DataType.S1615])  # ts / 10
        self.__du_th = du_th
        self.__tau_th = tau_th
        self.__v_thresh = v_thresh

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[DU_TH] = self.__du_th
        parameters[TAU_TH] = self.__tau_th
        parameters[V_THRESH] = self.__v_thresh

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractThresholdType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        # Add the rest of the data
        return [parameters[DU_TH].apply_operation(lambda x: 1.0 / x),
                parameters[TAU_TH].apply_operation(lambda x: 1.0 / x),
                parameters[V_THRESH], float(ts) / -10000.0]

    @overrides(AbstractThresholdType.update_values)
    def update_values(self, values, parameters, state_variables):
        pass

    @property
    def v_thresh(self):
        """
        :math:`V_{thresh}`
        """
        return self.__v_thresh

    @property
    def du_th(self):
        """
        :math:`du_{thresh}`
        """
        return self.__du_th

    @property
    def tau_th(self):
        r"""
        :math:`\tau_{thresh}`
        """
        return self.__tau_th
