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

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_EXC2 = "isyn_exc2"
ISYN_INH = "isyn_inh"
MULTIPLICATOR = "multiplicator"
EXC2_OLD = "exc2_old"
SCALING_FACTOR = "scaling_factor"
TIMESTEP_MS = "timestep_ms"


class SynapseTypeSEMD(AbstractSynapseType):
    __slots__ = [
        "__tau_syn_E",
        "__tau_syn_E2",
        "__tau_syn_I",
        "__isyn_exc",
        "__isyn_exc2",
        "__isyn_inh",
        "__multiplicator",
        "__exc2_old",
        "__scaling_factor"]

    def __init__(
            self, tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2,
            isyn_inh, multiplicator, exc2_old, scaling_factor):
        r"""
        :param tau_syn_E: :math:`\tau^{syn}_{e_1}`
        :type tau_syn_E:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param tau_syn_E2: :math:`\tau^{syn}_{e_2}`
        :type tau_syn_E2:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param tau_syn_I: :math:`\tau^{syn}_i`
        :type tau_syn_I:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param isyn_exc: :math:`I^{syn}_{e_1}`
        :type isyn_exc:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param isyn_exc2: :math:`I^{syn}_{e_2}`
        :type isyn_exc2:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param isyn_inh: :math:`I^{syn}_i`
        :type isyn_inh:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param multiplicator:
        :type multiplicator:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param exc2_old:
        :type exc2_old:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param scaling_factor:
        :type scaling_factor:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, TAU_SYN_E),
                (DataType.S1615, ISYN_EXC),
                (DataType.S1615, TAU_SYN_E2),
                (DataType.S1615, ISYN_EXC2),
                (DataType.S1615, TAU_SYN_I),
                (DataType.S1615, ISYN_INH),
                (DataType.S1615, MULTIPLICATOR),
                (DataType.S1615, EXC2_OLD),
                (DataType.S1615, SCALING_FACTOR),
                (DataType.S1615, TIMESTEP_MS)])],
            {TAU_SYN_E: "mV", TAU_SYN_E2: "mV", TAU_SYN_I: 'mV', ISYN_EXC: "",
             ISYN_EXC2: "", ISYN_INH: "", MULTIPLICATOR: "", EXC2_OLD: "",
             SCALING_FACTOR: ""})
        self.__tau_syn_E = tau_syn_E
        self.__tau_syn_E2 = tau_syn_E2
        self.__tau_syn_I = tau_syn_I
        self.__isyn_exc = isyn_exc
        self.__isyn_exc2 = isyn_exc2
        self.__isyn_inh = isyn_inh
        self.__multiplicator = multiplicator
        self.__exc2_old = exc2_old
        self.__scaling_factor = scaling_factor

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self.__tau_syn_E
        parameters[TAU_SYN_E2] = self.__tau_syn_E2
        parameters[TAU_SYN_I] = self.__tau_syn_I
        parameters[TIMESTEP_MS] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC] = self.__isyn_exc
        state_variables[ISYN_EXC2] = self.__isyn_exc2
        state_variables[ISYN_INH] = self.__isyn_inh
        state_variables[EXC2_OLD] = self.__exc2_old
        state_variables[MULTIPLICATOR] = self.__multiplicator
        state_variables[SCALING_FACTOR] = self.__scaling_factor

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 3

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory"

    @property
    def tau_syn_E(self):
        return self.__tau_syn_E

    @property
    def tau_syn_E2(self):
        return self.__tau_syn_E2

    @property
    def tau_syn_I(self):
        return self.__tau_syn_I

    @property
    def isyn_exc(self):
        return self.__isyn_exc

    @property
    def isyn_inh(self):
        return self.__isyn_inh

    @property
    def isyn_exc2(self):
        return self.__isyn_exc2

    @property
    def multiplicator(self):
        return self.__multiplicator

    @property
    def exc2_old(self):
        return self.__exc2_old

    @property
    def scaling_factor(self):
        return self.__scaling_factor
