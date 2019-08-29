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
from pacman.executor.injection_decorator import inject_items
from .abstract_synapse_type import AbstractSynapseType

TAU_SYN_E_SOMA = 'tau_syn_E_soma'
TAU_SYN_E_DENDRITE = 'tau_syn_E_dendrite'
TAU_SYN_I_SOMA = 'tau_syn_I_soma'
TAU_SYN_I_DENDRITE = 'tau_syn_I_dendrite'
ISYN_EXC_SOMA = "isyn_exc_soma"
ISYN_EXC_DENDRITE = "isyn_exc_dendrite"
ISYN_INH_SOMA = "isyn_inh_soma"
ISYN_INH_DENDRITE = "isyn_inh_dendrite"

UNITS = {
    TAU_SYN_E_SOMA: "mV",
    TAU_SYN_E_DENDRITE: "mV",
    TAU_SYN_I_SOMA: 'mV',
    TAU_SYN_I_DENDRITE: 'mV',
    ISYN_EXC_SOMA: "",
    ISYN_EXC_DENDRITE: "",
    ISYN_INH_SOMA: "",
    ISYN_INH_DENDRITE: "",
}


class SynapseTypeExponentialTwoComp(AbstractSynapseType):
    __slots__ = [
        "__tau_syn_E_soma",
        "__tau_syn_E_dendrite",
        "__tau_syn_I_soma",
        "__tau_syn_I_dendrite",
        "__isyn_exc_soma",
        "__isyn_exc_dendrite",
        "__isyn_inh_soma",
        "__isyn_inh_dendrite"
        ]

    def __init__(
            self, tau_syn_E_soma, tau_syn_E_dendrite, tau_syn_I_soma, tau_syn_I_dendrite,
            isyn_exc_soma, isyn_exc_dendrite, isyn_inh_soma, isyn_inh_dendrite):

        super(SynapseTypeExponentialTwoComp, self).__init__(
            [DataType.U032,    # decay_E_soma
             DataType.U032,    # init_E_soma
             DataType.S1615,   # isyn_exc_soma
             DataType.U032,    # decay_E_dendrite
             DataType.U032,    # init_E_dendrite
             DataType.S1615,   # isyn_exc_dendrite
             DataType.U032,    # decay_I_soma
             DataType.U032,    # init_I_soma
             DataType.S1615,   # isyn_inh_soma
             DataType.U032,    # decay_I_dendrite
             DataType.U032,    # init_I_dendrite
             DataType.S1615   # isyn_inh_dendrite
             ])
        self.__tau_syn_E_soma = tau_syn_E_soma
        self.__tau_syn_E_dendrite = tau_syn_E_dendrite
        self.__tau_syn_I_soma = tau_syn_I_soma
        self.__tau_syn_I_dendrite = tau_syn_I_dendrite
        self.__isyn_exc_soma = isyn_exc_soma
        self.__isyn_exc_dendrite = isyn_exc_dendrite
        self.__isyn_inh_soma = isyn_inh_soma
        self.__isyn_inh_dendrite = isyn_inh_dendrite

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100 * n_neurons

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E_SOMA] = self.__tau_syn_E_soma
        parameters[TAU_SYN_E_DENDRITE] = self.__tau_syn_E_dendrite
        parameters[TAU_SYN_I_SOMA] = self.__tau_syn_I_soma
        parameters[TAU_SYN_I_DENDRITE] = self.__tau_syn_I_dendrite

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC_SOMA] = self.__isyn_exc_soma
        state_variables[ISYN_EXC_DENDRITE] = self.__isyn_exc_dendrite
        state_variables[ISYN_INH_SOMA] = self.__isyn_inh_soma
        state_variables[ISYN_INH_DENDRITE] = self.__isyn_inh_dendrite

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractSynapseType.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        tsfloat = float(ts) / 1000.0
        decay = lambda x: numpy.exp(-tsfloat / x)  # noqa E731
        init = lambda x: (x / tsfloat) * (1.0 - numpy.exp(-tsfloat / x))  # noqa E731

        # Add the rest of the data
        return [parameters[TAU_SYN_E_SOMA].apply_operation(decay),
                parameters[TAU_SYN_E_SOMA].apply_operation(init),
                state_variables[ISYN_EXC_SOMA],
                parameters[TAU_SYN_E_DENDRITE].apply_operation(decay),
                parameters[TAU_SYN_E_DENDRITE].apply_operation(init),
                state_variables[ISYN_EXC_DENDRITE],
                parameters[TAU_SYN_I_SOMA].apply_operation(decay),
                parameters[TAU_SYN_I_SOMA].apply_operation(init),
                state_variables[ISYN_INH_SOMA],
                parameters[TAU_SYN_I_DENDRITE].apply_operation(decay),
                parameters[TAU_SYN_I_DENDRITE].apply_operation(init),
                state_variables[ISYN_INH_DENDRITE]
                ]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E_soma, _init_E_soma, isyn_exc_soma,
         _decay_E_dendrite, _init_E_dendrite, isyn_exc_dendrite,
         _decay_I_soma, _init_I_soma, isyn_inh_soma,
         _decay_I_dendrite, _init_I_dendrite, isyn_inh_dendrite) = values

        state_variables[ISYN_EXC_SOMA] = isyn_exc_soma
        state_variables[ISYN_EXC_DENDRITE] = isyn_exc_dendrite
        state_variables[ISYN_INH_SOMA] = isyn_inh_soma
        state_variables[ISYN_INH_DENDRITE] = isyn_inh_dendrite

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "soma_exc":
            return 0
        elif target == "dendrite_exc":
            return 1
        elif target == "soma_inh":
            return 2
        elif target == "dendrite_inh":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "soma_exc", "dendrite_exc", "soma_inh", "dendrite_inh"

    @property
    def tau_syn_E_soma(self):
        return self.__tau_syn_E_soma

    @tau_syn_E_soma.setter
    def tau_syn_E_soma(self, tau_syn_E_soma):
        self.__tau_syn_E_soma = tau_syn_E_soma

    @property
    def tau_syn_E_dendrite(self):
        return self.__tau_syn_E_dendrite

    @tau_syn_E_dendrite.setter
    def tau_syn_E_dendrite(self, tau_syn_E_dendrite):
        self.__tau_syn_E_dendrite = tau_syn_E_dendrite

    @property
    def tau_syn_I_soma(self):
        return self.__tau_syn_I_soma

    @tau_syn_I_soma.setter
    def tau_syn_I_soma(self, tau_syn_I_soma):
        self.__tau_syn_I_soma = tau_syn_I_soma

    @property
    def tau_syn_I_dendrite(self):
        return self.__tau_syn_I_dendrite

    @tau_syn_I_dendrite.setter
    def tau_syn_I_dendrite(self, tau_syn_I_dendrite):
        self.__tau_syn_I_dendrite = tau_syn_I_dendrite

    @property
    def isyn_exc_soma(self):
        return self.__isyn_exc_soma

    @isyn_exc_soma.setter
    def isyn_exc_soma(self, isyn_exc_soma):
        self.__isyn_exc_soma = isyn_exc_soma

    @property
    def isyn_exc_dendrite(self):
        return self.__isyn_exc_dendrite

    @isyn_exc_dendrite.setter
    def isyn_exc_dendrite(self, isyn_exc_dendrite):
        self.__isyn_exc_dendrite = isyn_exc_dendrite

    @property
    def isyn_inh_soma(self):
        return self.__isyn_inh_soma

    @isyn_inh_soma.setter
    def isyn_inh_soma(self, isyn_inh_soma):
        self.__isyn_inh_soma = isyn_inh_soma

    @property
    def isyn_inh_dendrite(self):
        return self.__isyn_inh_dendrite

    @isyn_inh_dendrite.setter
    def isyn_inh_dendrite(self, isyn_inh_dendrite):
        self.__isyn_inh_dendrite = isyn_inh_dendrite

