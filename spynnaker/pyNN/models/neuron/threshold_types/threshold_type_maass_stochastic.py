# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from .abstract_threshold_type import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

DU_TH = "du_th"
TAU_TH = "tau_th"
V_THRESH = "v_thresh"
TIMESTEP = "timestep"


class ThresholdTypeMaassStochastic(AbstractThresholdType):
    """
    A stochastic threshold.

    Habenschuss S, Jonke Z, Maass W. Stochastic computations in cortical
    microcircuit models. *PLoS Computational Biology.* 2013;9(11):e1003311.
    `doi:10.1371/journal.pcbi.1003311
    <https://doi.org/10.1371/journal.pcbi.1003311>`_
    """
    __slots__ = [
        "__du_th",
        "__tau_th",
        "__v_thresh"]

    def __init__(self, du_th, tau_th, v_thresh):
        r"""
        :param du_th: :math:`du_{thresh}`
        :type du_th: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_th: :math:`\tau_{thresh}`
        :type tau_th: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param v_thresh: :math:`V_{thresh}`
        :type v_thresh: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, DU_TH),
                (DataType.S1615, TAU_TH),
                (DataType.S1615, V_THRESH),
                (DataType.S1615, TIMESTEP)])],
            {DU_TH: "mV", TAU_TH: "ms", V_THRESH: "mV"})
        self.__du_th = du_th
        self.__tau_th = tau_th
        self.__v_thresh = v_thresh

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[DU_TH] = self.__du_th
        parameters[TAU_TH] = self.__tau_th
        parameters[V_THRESH] = self.__v_thresh
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
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
