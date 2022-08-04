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
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_INH = "isyn_inh"

UNITS = {
    TAU_SYN_E: "mV",
    TAU_SYN_I: 'mV',
    ISYN_EXC: "",
    ISYN_INH: "",
}


class SynapseTypeExpIzhikevichNeuromodulated(AbstractSynapseType):
    __slots__ = [
        "_tau_syn_E",
        "_tau_syn_I",
        "_isyn_exc",
        "_isyn_inh"]

    def __init__(self, tau_syn_E, tau_syn_I, isyn_exc, isyn_inh):
        r"""
        :param float tau_syn_E: :math:`\tau^{syn}_e`
        :param float tau_syn_I: :math:`\tau^{syn}_i`
        :param float isyn_exc: :math:`I^{syn}_e`
        :param float isyn_inh: :math:`I^{syn}_i`
        """
        super(SynapseTypeExpIzhikevichNeuromodulated, self).__init__([
            DataType.U032,    # decay_E
            DataType.U032,    # init_E
            DataType.S1615,   # isyn_exc
            DataType.U032,    # decay_I
            DataType.U032,    # init_I
            DataType.S1615])  # isyn_inh
        self._tau_syn_E = tau_syn_E
        self._tau_syn_I = tau_syn_I
        self._isyn_exc = isyn_exc
        self._isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self._tau_syn_E
        parameters[TAU_SYN_I] = self._tau_syn_I

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC] = self._isyn_exc
        state_variables[ISYN_INH] = self._isyn_inh

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
                parameters[TAU_SYN_I].apply_operation(decay),
                parameters[TAU_SYN_I].apply_operation(init),
                state_variables[ISYN_INH]]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E, _init_E, isyn_exc, _decay_I, _init_I, isyn_inh) = values

        state_variables[ISYN_EXC] = isyn_exc
        state_variables[ISYN_INH] = isyn_inh

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        elif target == "reward":
            return 2
        elif target == "punishment":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "inhibitory", "reward", "punishment"

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = tau_syn_E

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_I = tau_syn_I

    @property
    def isyn_exc(self):
        return self._isyn_exc

    @isyn_exc.setter
    def isyn_exc(self, isyn_exc):
        self._isyn_exc = isyn_exc

    @property
    def isyn_inh(self):
        return self._isyn_inh

    @isyn_inh.setter
    def isyn_inh(self, isyn_inh):
        self._isyn_inh = isyn_inh
