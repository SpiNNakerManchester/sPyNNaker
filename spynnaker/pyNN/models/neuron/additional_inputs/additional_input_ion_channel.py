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
from .abstract_additional_input import AbstractAdditionalInput
from quantities.constants.tau import tau_neutron_mass_ratio

# I_ALPHA = "i_alpha"
# I_CA2 = "i_ca2"
# TAU_CA2 = "tau_ca2"
# 
# UNITS = {
#     I_ALPHA: "nA",
#     I_CA2: "nA",
#     TAU_CA2: "ms"
# }

N = "n"
gK = "gK"
Ek = "Ek"
I_k = "I_k"


UNITS = {
    N: "",
    gK: "mS/mm2",
    Ek :"mV",
    I_k: "nA"
}

#     CURRENT: "nA",
#     ALPHA_N: "mV",
#     BETA_N: "mV",
#     TAU_N: "mV",
#     N_INF: "mV"

class AdditionalInputIonChannel(AbstractAdditionalInput):
#     __slots__ = [
#         "__tau_ca2",
#         "__i_ca2",
#         "__i_alpha"]
    __slots__ = [
        "__n",
        "__gK",
        "__Ek",
        "__I_k"]
    
#         "__current",
#         "__alpha_n",
#         "__beta_n",
#         "__tau_n",
#         "__n_inf"
        
#     def __init__(self,  tau_ca2, i_ca2, i_alpha):
#         super(AdditionalInputIonChannel, self).__init__([
#             DataType.S1615,   # e^(-ts / tau_ca2)
#             DataType.S1615,   # i_ca_2
#             DataType.S1615])  # i_alpha
#         self.__tau_ca2 = tau_ca2
#         self.__i_ca2 = i_ca2
#         self.__i_alpha = i_alpha

    def __init__(self,  n, gK, Ek, I_k):
        super(AdditionalInputIonChannel, self).__init__([
            DataType.S1615,   # n
            DataType.S1615,   # gk
            DataType.S1615,   # Ek
            DataType.S1615,   # I_k
            ]) 
#             DataType.S1615,   # beta_n
#             DataType.S1615,   # tau_n
#             DataType.S1615,   # n_inf
         # current
        self.__n = n
        self.__gK = gK
        self.__Ek = Ek
        self.__I_k = I_k
#         self.__beta_n = beta_n
#         self.__tau_n = tau_n
#         self.__n_inf = n_inf
        
                
    @overrides(AbstractAdditionalInput.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 3 * n_neurons

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):
        parameters[gK] = self.__gK
        parameters[Ek] = self.__Ek

    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[N] = self.__n
        state_variables[I_k] = self.I_k
#         state_variables[CURRENT] = self.__current
#         state_variables[ALPHA_N] = self.__alpha_n
#         state_variables[BETA_N] = self.__beta_n
#         state_variables[TAU_N] = self.__tau_n
#         state_variables[N_INF] = self.__n_inf
        

    @overrides(AbstractAdditionalInput.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractAdditionalInput.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractAdditionalInput.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        # pylint: disable=arguments-differ

        # Add the rest of the data
#         return [parameters[TAU_CA2].apply_operation(
#                     operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
#                 state_variables[I_CA2], parameters[I_ALPHA]]
        return [state_variables[N], parameters[gK], parameters[Ek], state_variables[I_k]]
#                 state_variables[ALPHA_N], state_variables[BETA_N], state_variables[TAU_N],
#                 state_variables[N_INF]]

    @overrides(AbstractAdditionalInput.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_n, _gK, _Ek, _I_k) = values
#         , _beta_n, _tau_n, _n_inf

        # Copy the changed data only
        state_variables[N] = n
        state_variables[I_k] = I_k
#         state_variables[ALPHA_N] = alpha_n
#         state_variables[BETA_N] = beta_n
#         state_variables[TAU_N] = tau_n
#         state_variables[N_INF] = n_inf
#         
    @property
    def n(self):
        return self.__n

    @n.setter
    def n(self, n):
        self.__n = n

    @property
    def gK(self):
        return self.__gK
    
    @gK.setter
    def gK(self, gK):
        self.__gK = gK
        
    @property
    def Ek(self):
        return self.__Ek

    @Ek.setter
    def Ek(self, Ek):
        self.__Ek = Ek

    @property
    def I_k(self):
        return self.__I_k

    @I_k.setter
    def I_k(self, I_k):
        self.__I_k = I_k
        
#     @property
#     def alpha_n(self):
#         return self.__alpha_n
# 
#     @alpha_n.setter
#     def alpha_n(self, alpha_n):
#         self.__alpha_n = alpha_n
#         
#     @property
#     def beta_n(self):
#         return self.__beta_n
# 
#     @beta_n.setter
#     def beta_n(self, beta_n):
#         self.__beta_n = beta_n
#         
#     @property
#     def tau_n(self):
#         return self.__tau_n
# 
#     @tau_n.setter
#     def tau_n(self, tau_n):
#         self.__tau_n = tau_n
#         
#     @property
#     def n_inf(self):
#         return self.__n_inf
# 
#     @n_inf.setter
#     def n_inf(self, n_inf):
#         self.__n_inf = n_inf
        
