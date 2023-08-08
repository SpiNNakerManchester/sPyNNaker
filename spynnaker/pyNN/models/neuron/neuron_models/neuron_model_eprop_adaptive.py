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
SYNAPSES_PER_NEURON = 250

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"

# eprop
PSI = "psi"
Z = "z"
A = "a"

# Threshold
BIG_B = "big_b"
SMALL_B = "small_b"
SMALL_B_0 = "small_b_0"
TAU_A = "tau_a"
BETA = "beta"
SCALAR = "scalar"

# Learning signal
L = "learning_signal"
W_FB = "feedback_weight"
WINDOW_SIZE = "window_size"
NUMBER_OF_CUES = "number_of_cues"

# eprop "global"
CORE_POP_RATE = "core_pop_rate"
TARGET_RATE = "target_rate"
TAU_ERR = "tau_err"
ETA = "eta"  # (global learning rate)

# eprop synapse
DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
EP_A = "ep_a"
E_BAR = "e_bar"
UPDATE_READY = "update_ready"


class NeuronModelEPropAdaptive(AbstractStandardNeuronComponent):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",
        "__z",
        "__a",
        "__psi",
        # threshold params
        "__B",
        "__small_b",
        "__small_b_0",
        "__tau_a",
        "__beta",
        "__scalar",
        # reg params
        "__target_rate",
        "__tau_err",
        # learning signal
        "__learning_signal",
        "__w_fb",
        "__window_size",
        "__number_of_cues",
        # eprop "global"
        "__core_pop_rate",
        "__core_target_rate",
        "__rate_exp_TC",
        "__eta"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            psi,
            # threshold params
            B, small_b, small_b_0, tau_a, beta,
            # regularisation params
            target_rate, tau_err, learning_signal, w_fb, window_size,
            number_of_cues,
            # eprop "global"
            eta
            ):
        # TODO: documentation of parameters

        struct_neuron_vals = [
            # neuron params
            (DataType.S1615, V),
            (DataType.S1615, V_REST),
            (DataType.S1615, CM),
            (DataType.S1615, TAU_M),
            (DataType.S1615, I_OFFSET),
            (DataType.S1615, V_RESET),
            (DataType.S1615, TAU_REFRAC),
            (DataType.INT32, REFRACT_TIMER),
            (DataType.S1615, TIMESTEP),
            (DataType.S1615, Z),
            (DataType.S1615, A),
            (DataType.S1615, PSI),  # psi, pseuo_derivative
            (DataType.S1615, BIG_B),
            (DataType.S1615, SMALL_B),
            (DataType.S1615, SMALL_B_0),
            (DataType.UINT32, TAU_A),
            (DataType.S1615, BETA),
            (DataType.S1615, SCALAR),
            (DataType.S1615, L),
            (DataType.S1615, W_FB),
            (DataType.UINT32, WINDOW_SIZE),
            (DataType.UINT32, NUMBER_OF_CUES),
            (DataType.S1615, CORE_POP_RATE),  # core_pop_rate
            (DataType.S1615, TARGET_RATE),  # core_target_rate
            (DataType.S1615, TAU_ERR),  # rate_exp_TC
            (DataType.S1615, ETA)]  # eta (learning rate)

        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                # eprop syn state
                [(DataType.S1615, DELTA_W+str(n)),  # delta_w
                 (DataType.S1615, Z_BAR_OLD+str(n)),  # z_bar_old
                 (DataType.S1615, Z_BAR+str(n)),  # z_bar
                 (DataType.S1615, EP_A+str(n)),  # ep_a
                 (DataType.S1615, E_BAR+str(n)),  # e_bar
                 (DataType.INT32, UPDATE_READY+str(n))])

        super().__init__(
            [Struct(
                struct_neuron_vals)],
            {V: 'mV', V_REST: 'mV', TAU_M: 'ms', CM: 'nF', I_OFFSET: 'nA',
             V_RESET: 'mV', TAU_REFRAC: 'ms', Z: '', A: '', PSI: '',
             BIG_B: 'mV', SMALL_B: 'mV', SMALL_B_0: 'mV', TAU_A: 'ms'})

        if v_init is None:
            v_init = v_rest
        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac
        self.__psi = psi

        # threshold params
        self.__B = B
        self.__small_b = small_b
        self.__small_b_0 = small_b_0
        self.__tau_a = tau_a
        self.__beta = beta
        self.__scalar = 1000

        # Regularisation params
        self.__target_rate = target_rate
        self.__tau_err = tau_err

        # learning signal
        self.__learning_signal = learning_signal
        self.__w_fb = w_fb
        self.__window_size = window_size
        self.__number_of_cues = number_of_cues

        # eprop "global"
        self.__eta = eta

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

        parameters[SMALL_B_0] = self.__small_b_0
        parameters[TAU_A] = self.__tau_a
        parameters[BETA] = self.__beta
        parameters[SCALAR] = self.__scalar
        parameters[W_FB] = self.__w_fb
        parameters[WINDOW_SIZE] = self.__window_size
        parameters[NUMBER_OF_CUES] = self.__number_of_cues

        # Are these parameters or variables?
        parameters[CORE_POP_RATE] = 0.0  # initialise here, not in C
        parameters[TARGET_RATE] = self.__target_rate
        parameters[TAU_ERR] = self.__tau_err
        parameters[ETA] = self.__eta

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0
        state_variables[PSI] = self.__psi
        state_variables[Z] = 0  # initialise to zero
        state_variables[A] = 0  # initialise to zero

        state_variables[BIG_B] = self.__B
        state_variables[SMALL_B] = self.__small_b

        state_variables[L] = self.__learning_signal

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            state_variables[EP_A+str(n)] = 0
            state_variables[E_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self.__window_size

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
    def B(self):
        return self.__B

    @B.setter
    def B(self, new_value):
        self.__B = new_value

    @property
    def small_b(self):
        return self.__small_b

    @small_b.setter
    def small_b(self, new_value):
        self.__small_b = new_value

    @property
    def small_b_0(self):
        return self.__small_b_0

    @small_b_0.setter
    def small_b_0(self, new_value):
        self.__small_b_0 = new_value

    @property
    def tau_a(self):
        return self.__tau_a

    @tau_a.setter
    def tau_a(self, new_value):
        self.__tau_a = new_value

    @property
    def beta(self):
        return self.__beta

    @beta.setter
    def beta(self, new_value):
        self.__beta = new_value

    @property
    def w_fb(self):
        return self.__w_fb

    @w_fb.setter
    def w_fb(self, new_value):
        self.__w_fb = new_value

    @property
    def window_size(self):
        return self.__window_size

    @window_size.setter
    def window_size(self, new_value):
        self.__window_size = new_value

    @property
    def number_of_cues(self):
        return self.__number_of_cues

    @number_of_cues.setter
    def number_of_cues(self, new_value):
        self.__number_of_cues = new_value

    @overrides(AbstractStandardNeuronComponent.uses_eprop)
    @property
    def uses_eprop(self):
        return True
