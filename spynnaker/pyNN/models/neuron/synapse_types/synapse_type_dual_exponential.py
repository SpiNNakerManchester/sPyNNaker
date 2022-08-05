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

import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_synapse_type import AbstractSynapseType

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_EXC2 = "isyn_exc2"
ISYN_INH = "isyn_inh"

UNITS = {
    TAU_SYN_E: "mV",
    TAU_SYN_E2: "mV",
    TAU_SYN_I: 'mV',
    ISYN_EXC: "",
    ISYN_EXC2: "",
    ISYN_INH: "",
}


class SynapseTypeDualExponential(AbstractSynapseType):
    __slots__ = [
        "__tau_syn_E",
        "__tau_syn_E2",
        "__tau_syn_I",
        "__isyn_exc",
        "__isyn_exc2",
        "__isyn_inh"]

    def __init__(
            self, tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2,
            isyn_inh):
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
        """
        super().__init__(
            [DataType.U032,    # decay_E
             DataType.U032,    # init_E
             DataType.S1615,   # isyn_exc
             DataType.U032,    # decay_E2
             DataType.U032,    # init_E2
             DataType.S1615,   # isyn_exc2
             DataType.U032,    # decay_I
             DataType.U032,    # init_I
             DataType.S1615])  # isyn_inh
        self.__tau_syn_E = tau_syn_E
        self.__tau_syn_E2 = tau_syn_E2
        self.__tau_syn_I = tau_syn_I
        self.__isyn_exc = isyn_exc
        self.__isyn_exc2 = isyn_exc2
        self.__isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self.__tau_syn_E
        parameters[TAU_SYN_E2] = self.__tau_syn_E2
        parameters[TAU_SYN_I] = self.__tau_syn_I

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC] = self.__isyn_exc
        state_variables[ISYN_EXC2] = self.__isyn_exc2
        state_variables[ISYN_INH] = self.__isyn_inh

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractSynapseType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param int ts: machine time step
        """
        tsfloat = float(ts) / 1000.0
        decay = lambda x: numpy.exp(-tsfloat / x)  # noqa E731
        init = lambda x: (x / tsfloat) * (1.0 - numpy.exp(-tsfloat / x))  # noqa E731

        # Add the rest of the data
        return [parameters[TAU_SYN_E].apply_operation(decay),
                parameters[TAU_SYN_E].apply_operation(init),
                state_variables[ISYN_EXC],
                parameters[TAU_SYN_E2].apply_operation(decay),
                parameters[TAU_SYN_E2].apply_operation(init),
                state_variables[ISYN_EXC2],
                parameters[TAU_SYN_I].apply_operation(decay),
                parameters[TAU_SYN_I].apply_operation(init),
                state_variables[ISYN_INH]]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E, _init_E, isyn_exc, _decay_E2, _init_E2, isyn_exc2,
         _decay_I, _init_I, isyn_inh) = values

        state_variables[ISYN_EXC] = isyn_exc
        state_variables[ISYN_EXC2] = isyn_exc2
        state_variables[ISYN_INH] = isyn_inh

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
