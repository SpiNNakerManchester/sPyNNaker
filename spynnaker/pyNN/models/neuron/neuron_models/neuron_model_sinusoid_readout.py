# Copyright (c) 2019 The University of Manchester
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
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

# constants
SYNAPSES_PER_NEURON = 250   # around 415 with only 3 in syn_state

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"
TARGET_DATA = "target_data"
# Learning signal
L = "learning_signal"
W_FB = "feedback_weight"
ETA = "eta"

# eprop synapse
DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
UPDATE_READY = "update_ready"


class NeuronModelLeakyIntegrateAndFireSinusoidReadout(
        AbstractStandardNeuronComponent):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",
        "__target_data",

        # learning signal
        "__learning_signal",
        "__w_fb",
        "__eta",
        "__update_ready"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            target_data, learning_signal, w_fb, eta, update_ready):

        struct_neuron_vals = [
            (DataType.S1615, V),  # v
            (DataType.S1615, V_REST),  # v_rest
            (DataType.S1615, CM),  # r_membrane (= tau_m / cm)
            (DataType.S1615, TAU_M),  # exp_tc (= e^(-ts / tau_m))
            (DataType.S1615, I_OFFSET),  # i_offset
            (DataType.S1615, V_RESET),  # v_reset
            (DataType.S1615, TAU_REFRAC),  # tau_refrac
            (DataType.INT32, REFRACT_TIMER),  # count_refrac
            (DataType.S1615, TIMESTEP),  # timestep
            # Learning signal
            (DataType.S1615, L),  # L
            (DataType.S1615, W_FB)  # w_fb
        ]

        # former global parameters
        for n in range(1024):
            struct_neuron_vals.extend(
                [(DataType.S1615, TARGET_DATA+str(n))])
        struct_neuron_vals.extend([(DataType.S1615, ETA)])

        # Synapse states - always initialise to zero
        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                # eprop_syn_state
                [(DataType.S1615, DELTA_W+str(n)),  # delta_w
                 (DataType.S1615, Z_BAR_OLD+str(n)),  # z_bar_old
                 (DataType.S1615, Z_BAR+str(n)),  # z_bar
                 (DataType.UINT32, UPDATE_READY+str(n))])  # update_ready

        super().__init__(
            [Struct(struct_neuron_vals)],
            {V: 'mV', V_REST: 'mV', TAU_M: 'ms', CM: 'nF', I_OFFSET: 'nA',
             V_RESET: 'mV', TAU_REFRAC: 'ms'})

        if v_init is None:
            v_init = v_rest

        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac
        self.__target_data = target_data

        # learning signal
        self.__learning_signal = learning_signal
        self.__w_fb = w_fb

        self.__eta = eta

        self.__update_ready = update_ready

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

        # learning params
        parameters[W_FB] = self.__w_fb

        # Target data (formerly global data)
        for n in range(1024):
            parameters[TARGET_DATA+str(n)] = self.__target_data[n]

        parameters[ETA] = self.__eta

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0

        # learning params
        state_variables[L] = self.__learning_signal

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self.__update_ready

    @property
    def target_data(self):
        return self.__target_data

    @target_data.setter
    def target_data(self, target_data):
        self.__target_data = target_data

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

    @property
    def w_fb(self):
        return self.__w_fb

    @w_fb.setter
    def w_fb(self, w_fb):
        self.__w_fb = w_fb

    @overrides(AbstractStandardNeuronComponent.uses_eprop)
    @property
    def uses_eprop(self):
        return True
