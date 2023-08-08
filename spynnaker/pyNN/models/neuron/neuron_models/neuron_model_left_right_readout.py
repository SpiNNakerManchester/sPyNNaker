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
SYNAPSES_PER_NEURON = 250   # around 415 with only 3 in syn_state (?)

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
# COUNT_REFRAC = "count_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"

# Learning signal
L = "learning_signal"
W_FB = "feedback_weight"
WINDOW_SIZE = "window_size"

SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"
SEED4 = "seed4"
TICKS_PER_SECOND = "ticks_per_second"
TIME_SINCE_LAST_SPIKE = "time_since_last_spike"
RATE_AT_LAST_SETTING = "rate_at_last_setting"
MEAN_L = "mean_l"
MEAN_R = "mean_r"
RATE_ON = "rate_on"
RATE_OFF = "rate_off"
POISSON_POP_SIZE = 'poisson_pop_size'
POISSON_KEY = 'poisson_key'
CROSS_ENTROPY = 'cross_entropy'
ETA = 'eta'
NUMBER_OF_CUES = 'number_of_cues'

DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
UPDATE_READY = "update_ready"


class NeuronModelLeftRightReadout(AbstractStandardNeuronComponent):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",
        "__rate_off",
        "__rate_on",
        "__learning_signal",
        "__w_fb",
        "__window_size",
        "__eta",
        "__mean_l",
        "__mean_r",
        "__cross_entropy",
        "__poisson_key",
        "__poisson_pop_size",
        "__number_of_cues"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            rate_on, rate_off, poisson_pop_size, learning_signal, w_fb, eta,
            window_size, number_of_cues):

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
            (DataType.S1615, L),  # Learning_signal
            (DataType.S1615, W_FB),  # w_fb
            (DataType.UINT32, WINDOW_SIZE),  # window_size
            # former global parameters
            (DataType.UINT32, SEED1),
            (DataType.UINT32, SEED2),
            (DataType.UINT32, SEED3),
            (DataType.UINT32, SEED4),
            (DataType.S1615, TICKS_PER_SECOND),
            (DataType.S1615, TIME_SINCE_LAST_SPIKE),
            (DataType.S1615, RATE_AT_LAST_SETTING),
            (DataType.S1615, RATE_ON),
            (DataType.S1615, RATE_OFF),
            (DataType.S1615, MEAN_L),
            (DataType.S1615, MEAN_R),
            (DataType.S1615, CROSS_ENTROPY),
            (DataType.UINT32, POISSON_KEY),
            (DataType.UINT32, POISSON_POP_SIZE),
            (DataType.S1615, ETA),
            (DataType.UINT32, NUMBER_OF_CUES)
        ]

        # Synapse states - always initialise to zero
        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                [(DataType.S1615, DELTA_W+str(n)),
                 (DataType.S1615, Z_BAR_OLD+str(n)),
                 (DataType.S1615, Z_BAR+str(n)),
                 (DataType.UINT32, UPDATE_READY+str(n))])

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
        self.__rate_off = rate_off
        self.__rate_on = rate_on
        self.__mean_l = 0.0
        self.__mean_r = 0.0
        self.__cross_entropy = 0.0
        self.__poisson_key = 0  # None TODO: work out how to pass this in
        self.__poisson_pop_size = poisson_pop_size
        self.__learning_signal = learning_signal
        self.__w_fb = w_fb
        self.__eta = eta
        self.__window_size = window_size
        self.__number_of_cues = number_of_cues

    def set_poisson_key(self, p_key):
        self.__poisson_key = p_key

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

        parameters[L] = self.__learning_signal
        parameters[W_FB] = self.__w_fb
        parameters[WINDOW_SIZE] = self.__window_size
        # These should probably have defaults earlier than this
        # TODO: some confusion as to which values were actually being used?
        parameters[SEED1] = 1  # 10065
        parameters[SEED2] = 2  # 232
        parameters[SEED3] = 3  # 3634
        parameters[SEED4] = 4  # 4877

        parameters[RATE_ON] = self.__rate_on
        parameters[RATE_OFF] = self.__rate_off

        parameters[TICKS_PER_SECOND] = 0.0
        parameters[TIME_SINCE_LAST_SPIKE] = 0.0
        parameters[RATE_AT_LAST_SETTING] = 0.0
        parameters[POISSON_POP_SIZE] = self.__poisson_pop_size
        parameters[MEAN_L] = self.__mean_l
        parameters[MEAN_R] = self.__mean_r
        parameters[CROSS_ENTROPY] = self.__cross_entropy
        parameters[POISSON_KEY] = self.__poisson_key
        parameters[POISSON_POP_SIZE] = self.__poisson_pop_size
        parameters[ETA] = self.__eta
        parameters[NUMBER_OF_CUES] = self.__number_of_cues

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
            state_variables[UPDATE_READY+str(n)] = self.__window_size

    @property
    def rate_on(self):
        return self.__rate_on

    @rate_on.setter
    def rate_on(self, rate_on):
        self.__rate_on = rate_on

    @property
    def rate_off(self):
        return self.__rate_off

    @rate_on.setter
    def rate_on(self, rate_off):
        self.__rate_off = rate_off

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
    def w_fb(self, new_value):
        self.__w_fb = new_value

    @property
    def window_size(self):
        return self.__window_size

    @window_size.setter
    def window_size(self, new_value):
        self.__window_size = new_value

    @overrides(AbstractStandardNeuronComponent.uses_eprop)
    @property
    def uses_eprop(self):
        return True
