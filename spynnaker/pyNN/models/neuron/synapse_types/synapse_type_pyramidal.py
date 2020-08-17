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

TAU_SYN_E_APICAL = 'tau_syn_E_apical'
TAU_SYN_E_BASAL = 'tau_syn_E_basal'
TAU_SYN_I_APICAL = 'tau_syn_I_apical'
TAU_SYN_I_BASAL = 'tau_syn_I_basal'
ISYN_EXC_APICAL = "isyn_exc_apical"
ISYN_EXC_BASAL = "isyn_exc_basal"
ISYN_INH_APICAL = "isyn_inh_apical"
ISYN_INH_BASAL = "isyn_inh_basal"

UNITS = {
    TAU_SYN_E_APICAL: "mV",
    TAU_SYN_E_BASAL: "mV",
    TAU_SYN_I_APICAL: 'mV',
    TAU_SYN_I_BASAL: 'mV',
    ISYN_EXC_APICAL: "",
    ISYN_EXC_BASAL: "",
    ISYN_INH_APICAL: "",
    ISYN_INH_BASAL: "",
}


class SynapseTypePyramidal(AbstractSynapseType):
    __slots__ = [
        "__tau_syn_E_apical",
        "__tau_syn_E_basal",
        "__tau_syn_I_apical",
        "__tau_syn_I_basal",
        "__isyn_exc_apical",
        "__isyn_exc_basal",
        "__isyn_inh_apical",
        "__isyn_inh_basal"
        ]

    def __init__(
            self, tau_syn_E_apical, tau_syn_E_basal, tau_syn_I_apical, tau_syn_I_basal,
            isyn_exc_apical, isyn_exc_basal, isyn_inh_apical, isyn_inh_basal):

        super(SynapseTypePyramidal, self).__init__(
            [DataType.U032,    # decay_E_apical
             DataType.U032,    # init_E_apical
             DataType.S1615,   # isyn_exc_apical
             DataType.U032,    # decay_E_basal
             DataType.U032,    # init_E_basal
             DataType.S1615,   # isyn_exc_basal
             DataType.U032,    # decay_I_apical
             DataType.U032,    # init_I_apical
             DataType.S1615,   # isyn_inh_apical
             DataType.U032,    # decay_I_basal
             DataType.U032,    # init_I_basal
             DataType.S1615   # isyn_inh_basal
             ])
        self.__tau_syn_E_apical = tau_syn_E_apical
        self.__tau_syn_E_basal = tau_syn_E_basal
        self.__tau_syn_I_apical = tau_syn_I_apical
        self.__tau_syn_I_basal = tau_syn_I_basal
        self.__isyn_exc_apical = isyn_exc_apical
        self.__isyn_exc_basal = isyn_exc_basal
        self.__isyn_inh_apical = isyn_inh_apical
        self.__isyn_inh_basal = isyn_inh_basal

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100 * n_neurons

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E_APICAL] = self.__tau_syn_E_apical
        parameters[TAU_SYN_E_BASAL] = self.__tau_syn_E_basal
        parameters[TAU_SYN_I_APICAL] = self.__tau_syn_I_apical
        parameters[TAU_SYN_I_BASAL] = self.__tau_syn_I_basal

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC_APICAL] = self.__isyn_exc_apical
        state_variables[ISYN_EXC_BASAL] = self.__isyn_exc_basal
        state_variables[ISYN_INH_APICAL] = self.__isyn_inh_apical
        state_variables[ISYN_INH_BASAL] = self.__isyn_inh_basal

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
        return [parameters[TAU_SYN_E_APICAL].apply_operation(decay),
                parameters[TAU_SYN_E_APICAL].apply_operation(init),
                state_variables[ISYN_EXC_APICAL],
                parameters[TAU_SYN_E_BASAL].apply_operation(decay),
                parameters[TAU_SYN_E_BASAL].apply_operation(init),
                state_variables[ISYN_EXC_BASAL],
                parameters[TAU_SYN_I_APICAL].apply_operation(decay),
                parameters[TAU_SYN_I_APICAL].apply_operation(init),
                state_variables[ISYN_INH_APICAL],
                parameters[TAU_SYN_I_BASAL].apply_operation(decay),
                parameters[TAU_SYN_I_BASAL].apply_operation(init),
                state_variables[ISYN_INH_BASAL]
                ]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E_apical, _init_E_apical, isyn_exc_apical,
         _decay_E_basal, _init_E_basal, isyn_exc_basal,
         _decay_I_apical, _init_I_apical, isyn_inh_apical,
         _decay_I_basal, _init_I_basal, isyn_inh_basal) = values

        state_variables[ISYN_EXC_APICAL] = isyn_exc_apical
        state_variables[ISYN_EXC_BASAL] = isyn_exc_basal
        state_variables[ISYN_INH_APICAL] = isyn_inh_apical
        state_variables[ISYN_INH_BASAL] = isyn_inh_basal

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "apical_exc":
            return 0
        elif target == "basal_exc":
            return 1
        elif target == "apical_inh":
            return 2
        elif target == "basal_inh":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "apical_exc", "basal_exc", "apical_inh", "basal_inh"

    @property
    def tau_syn_E_apical(self):
        return self.__tau_syn_E_apical

    @tau_syn_E_apical.setter
    def tau_syn_E_apical(self, tau_syn_E_apical):
        self.__tau_syn_E_apical = tau_syn_E_apical

    @property
    def tau_syn_E_basal(self):
        return self.__tau_syn_E_basal

    @tau_syn_E_basal.setter
    def tau_syn_E_basal(self, tau_syn_E_basal):
        self.__tau_syn_E_basal = tau_syn_E_basal

    @property
    def tau_syn_I_apical(self):
        return self.__tau_syn_I_apical

    @tau_syn_I_apical.setter
    def tau_syn_I_apical(self, tau_syn_I_apical):
        self.__tau_syn_I_apical = tau_syn_I_apical

    @property
    def tau_syn_I_basal(self):
        return self.__tau_syn_I_basal

    @tau_syn_I_basal.setter
    def tau_syn_I_basal(self, tau_syn_I_basal):
        self.__tau_syn_I_basal = tau_syn_I_basal

    @property
    def isyn_exc_apical(self):
        return self.__isyn_exc_apical

    @isyn_exc_apical.setter
    def isyn_exc_apical(self, isyn_exc_apical):
        self.__isyn_exc_apical = isyn_exc_apical

    @property
    def isyn_exc_basal(self):
        return self.__isyn_exc_basal

    @isyn_exc_basal.setter
    def isyn_exc_basal(self, isyn_exc_basal):
        self.__isyn_exc_basal = isyn_exc_basal

    @property
    def isyn_inh_apical(self):
        return self.__isyn_inh_apical

    @isyn_inh_apical.setter
    def isyn_inh_apical(self, isyn_inh_apical):
        self.__isyn_inh_apical = isyn_inh_apical

    @property
    def isyn_inh_basal(self):
        return self.__isyn_inh_basal

    @isyn_inh_basal.setter
    def isyn_inh_basal(self, isyn_inh_basal):
        self.__isyn_inh_basal = isyn_inh_basal

