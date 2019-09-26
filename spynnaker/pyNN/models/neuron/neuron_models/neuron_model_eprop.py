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
from .abstract_neuron_model import AbstractNeuronModel

# constants
SYNAPSES_PER_NEURON = 250



V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"
PSI = "psi"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms',
    PSI: 'N/A'
}


class NeuronModelEProp(AbstractNeuronModel):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",
        "__psi",
        "__target_rate",
        "__tau_err"]

    def __init__(
            self, 
            v_init, 
            v_rest, 
            tau_m, 
            cm, 
            i_offset, 
            v_reset, 
            tau_refrac,
            psi,
            # regularisation params
            target_rate,
            tau_err
            ):
        
        datatype_list = [
            DataType.S1615,   #  v
            DataType.S1615,   #  v_rest
            DataType.S1615,   #  r_membrane (= tau_m / cm)
            DataType.S1615,   #  exp_tc (= e^(-ts / tau_m))
            DataType.S1615,   #  i_offset
            DataType.INT32,   #  count_refrac
            DataType.S1615,   #  v_reset
            DataType.INT32,   #  tau_refrac
            DataType.S1615    #  psi, pseuo_derivative
            ] 
        
        # Synapse states - always initialise to zero
        eprop_syn_state = [ # synaptic state, one per synapse (kept in DTCM)
                DataType.INT16, # delta_w
                DataType.INT16, # z_bar
                DataType.INT32, # ep_a
                DataType.INT32, # e_bar
            ]
        # Extend to include fan-in for each neuron
        datatype_list.extend(eprop_syn_state * SYNAPSES_PER_NEURON)
        
        
        global_data_types = [
            DataType.S1615,   #  core_pop_rate 
            DataType.S1615,   #  core_target_rate
            DataType.S1615    #  rate_exp_TC
            ]
        
        super(NeuronModelEProp, self).__init__(data_types=datatype_list,
                                               global_data_types=global_data_types)

        if v_init is None:
            v_init = v_rest
        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac
        self.__psi = psi # calculate from v and v_thresh (but will probably end up zero)
        
        self.__target_rate = target_rate
        self.__tau_err = tau_err
        

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[COUNT_REFRAC] = 0
        state_variables[PSI] = self.__psi

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        values = [state_variables[V], 
                  parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], 
                state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),
                state_variables[PSI]
                ]
        
        # create synaptic state - init all state to zero
        eprop_syn_init = [0,
                          0,
                          0,
                          0]
        # extend to appropriate fan-in
        values.extend(eprop_syn_init * SYNAPSES_PER_NEURON)
        
        return values

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values, 
               additional_arguments={'ts'})
    def get_global_values(self, ts):
        glob_vals = [
            self.__target_rate,     #  initialise global pop rate to the target
            self.__target_rate,     #  set target rate
            numpy.exp(-float(ts/1000)/self.__tau_err)
            ]
        
        print("\n ")
        print(glob_vals)
        print(ts)
        print("\n")
        return glob_vals
        

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac, psi) = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[COUNT_REFRAC] = count_refrac
        state_vairables[PSI] = psi
    

    
    
    @property
    def v_init(self):
        return self.__v_init

    @v_init.setter
    def v_init(self, v_init):
        self.__v_init = v_init

    @property
    def v_rest(self):
        return self.__v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self.__v_rest = v_rest

    @property
    def tau_m(self):
        return self.__tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self.__tau_m = tau_m

    @property
    def cm(self):
        return self.__cm

    @cm.setter
    def cm(self, cm):
        self.__cm = cm

    @property
    def i_offset(self):
        return self.__i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self.__i_offset = i_offset

    @property
    def v_reset(self):
        return self.__v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self.__v_reset = v_reset

    @property
    def tau_refrac(self):
        return self.__tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self.__tau_refrac = tau_refrac
