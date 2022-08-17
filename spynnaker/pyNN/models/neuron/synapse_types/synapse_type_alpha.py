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
from .abstract_synapse_type import AbstractSynapseType
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

EXC_RESPONSE = "exc_response"
EXC_EXP_RESPONSE = "exc_exp_response"
TAU_SYN_E = "tau_syn_E"
INH_RESPONSE = "inh_response"
INH_EXP_RESPONSE = "inh_exp_response"
TAU_SYN_I = "tau_syn_I"
Q_EXC = "q_exc"
Q_INH = "q_inh"
TIMESTEP_MS = "timestep_ms"


class SynapseTypeAlpha(AbstractSynapseType):
    __slots__ = [
        "__exc_exp_response",
        "__exc_response",
        "__inh_exp_response",
        "__inh_response",
        "__tau_syn_E",
        "__tau_syn_I",
        "__q_exc",
        "__q_inh"]

    def __init__(self, exc_response, exc_exp_response,
                 tau_syn_E, inh_response, inh_exp_response, tau_syn_I):
        r"""
        :param exc_response: :math:`response^\mathrm{linear}_e`
        :type exc_response:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param exc_exp_response: :math:`response^\mathrm{exponential}_e`
        :type exc_exp_response:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param tau_syn_E: :math:`\tau^{syn}_e`
        :type tau_syn_E:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param inh_response: :math:`response^\mathrm{linear}_i`
        :type inh_response:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param inh_exp_response: :math:`response^\mathrm{exponential}_i`
        :type inh_exp_response:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param tau_syn_I: :math:`\tau^{syn}_i`
        :type tau_syn_I:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, EXC_RESPONSE),
                (DataType.S1615, EXC_EXP_RESPONSE),
                (DataType.S1615, TAU_SYN_E),
                (DataType.S1615, Q_EXC),
                (DataType.S1615, INH_RESPONSE),
                (DataType.S1615, INH_EXP_RESPONSE),
                (DataType.S1615, TAU_SYN_I),
                (DataType.S1615, Q_INH),
                (DataType.S1615, TIMESTEP_MS)])],
            {EXC_RESPONSE: "", EXC_EXP_RESPONSE: "", TAU_SYN_E: "ms",
             INH_RESPONSE: "", INH_EXP_RESPONSE: "", TAU_SYN_I: "ms"})

        # pylint: disable=too-many-arguments
        self.__exc_response = exc_response
        self.__exc_exp_response = exc_exp_response
        self.__tau_syn_E = tau_syn_E
        self.__inh_response = inh_response
        self.__inh_exp_response = inh_exp_response
        self.__tau_syn_I = tau_syn_I

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self.__tau_syn_E
        parameters[TAU_SYN_I] = self.__tau_syn_I

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[EXC_RESPONSE] = self.__exc_response
        state_variables[EXC_EXP_RESPONSE] = self.__exc_exp_response
        state_variables[Q_EXC] = 0
        state_variables[INH_RESPONSE] = self.__inh_response
        state_variables[INH_EXP_RESPONSE] = self.__inh_exp_response
        state_variables[Q_INH] = 0
        state_variables[TIMESTEP_MS] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 2  # EX and IH

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "inhibitory"

    @property
    def exc_response(self):
        return self.__exc_response

    @exc_response.setter
    def exc_response(self, exc_response):
        self.__exc_response = exc_response

    @property
    def tau_syn_E(self):
        return self.__tau_syn_E

    @property
    def inh_response(self):
        return self.__inh_response

    @property
    def tau_syn_I(self):
        return self.__tau_syn_I
