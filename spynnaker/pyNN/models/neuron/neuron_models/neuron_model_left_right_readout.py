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
from spinn_utilities.ranged import RangeDictionary

from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModel
from spynnaker.pyNN.utilities.struct import Struct

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


class NeuronModelLeftRightReadout(NeuronModel):
    """ Leaky integrate and fire neuron model with left/right readout. """

    __slots__ = [
        "__cm",
        "__cross_entropy",
        "__eta",
        "__i_offset",
        "__learning_signal",
        "__mean_l",
        "__mean_r",
        "__number_of_cues",
        "__poisson_key",
        "__poisson_pop_size",
        "__rate_off",
        "__rate_on",
        "__tau_m",
        "__tau_refrac",
        "__v_init",
        "__v_reset",
        "__v_rest",
        "__w_fb",
        "__window_size",
        ]

    def __init__(
            self, v_init: ModelParameter, v_rest: ModelParameter,
            tau_m: ModelParameter, cm: ModelParameter,
            i_offset: ModelParameter, v_reset: ModelParameter,
            tau_refrac: ModelParameter,
            rate_on: ModelParameter, rate_off: ModelParameter,
            poisson_pop_size: ModelParameter, learning_signal: ModelParameter,
            w_fb: ModelParameter, eta: ModelParameter,
            window_size: ModelParameter,
            number_of_cues: ModelParameter) -> None:
        """
        :param v_init: Initial membrane voltage (mV)
        :param v_rest: Resting membrane voltage (mV)
        :param tau_m: Membrane time constant (ms)
        :param cm: Membrane capacitance (nF)
        :param i_offset: Offset current (nA)
        :param v_reset: Reset voltage (mV)
        :param tau_refrac: Refractory period (ms)
        :param rate_on: Rate when the neuron is active
        :param rate_off: Rate when the neuron is inactive
        :param poisson_pop_size: Size of the Poisson population
        :param learning_signal: Learning signal for the readout
        :param w_fb: Feedback weight for the readout
        :param eta: Learning rate for the readout
        :param window_size: Size of the learning window
        :param number_of_cues: Number of cues for the readout
        """

        struct_neuron_vals = [
            (DataType.S1615, V),
            (DataType.S1615, V_REST),
            (DataType.S1615, CM),
            (DataType.S1615, TAU_M),
            (DataType.S1615, I_OFFSET),
            (DataType.S1615, V_RESET),
            (DataType.S1615, TAU_REFRAC),
            (DataType.INT32, REFRACT_TIMER),
            (DataType.S1615, TIMESTEP),
            # Learning signal
            (DataType.S1615, L),
            (DataType.S1615, W_FB),
            (DataType.UINT32, WINDOW_SIZE),
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

    def set_poisson_key(self, p_key: int) -> None:
        """ Set the Poisson key for the neuron model. """
        self.__poisson_key = p_key

    @overrides(NeuronModel.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        parameters[V_REST] = self._convert(self.__v_rest)
        parameters[TAU_M] = self._convert(self.__tau_m)
        parameters[CM] = self._convert(self.__cm)
        parameters[I_OFFSET] = self._convert(self.__i_offset)
        parameters[V_RESET] = self._convert(self.__v_reset)
        parameters[TAU_REFRAC] = self._convert(self.__tau_refrac)
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

        parameters[L] = self._convert(self.__learning_signal)
        parameters[W_FB] = self._convert(self.__w_fb)
        parameters[WINDOW_SIZE] = self._convert(self.__window_size)
        # These should probably have defaults earlier than this
        # TODO: some confusion as to which values were actually being used?
        parameters[SEED1] = 1  # 10065
        parameters[SEED2] = 2  # 232
        parameters[SEED3] = 3  # 3634
        parameters[SEED4] = 4  # 4877

        parameters[RATE_ON] = self._convert(self.__rate_on)
        parameters[RATE_OFF] = self._convert(self.__rate_off)

        parameters[TICKS_PER_SECOND] = 0.0
        parameters[TIME_SINCE_LAST_SPIKE] = 0.0
        parameters[RATE_AT_LAST_SETTING] = 0.0
        parameters[POISSON_POP_SIZE] = self._convert(self.__poisson_pop_size)
        parameters[MEAN_L] = self._convert(self.__mean_l)
        parameters[MEAN_R] = self._convert(self.__mean_r)
        parameters[CROSS_ENTROPY] = self._convert(self.__cross_entropy)
        parameters[POISSON_KEY] = self._convert(self.__poisson_key)
        parameters[POISSON_POP_SIZE] = self._convert(self.__poisson_pop_size)
        parameters[ETA] = self._convert(self.__eta)
        parameters[NUMBER_OF_CUES] = self._convert(self.__number_of_cues)

    @overrides(NeuronModel.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables[V] = self._convert(self.__v_init)
        state_variables[REFRACT_TIMER] = 0

        # learning params
        state_variables[L] = self._convert(self.__learning_signal)

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self._convert(
                self.__window_size)

    @property
    def rate_on(self) -> ModelParameter:
        """ Get the rate when the neuron is active. """
        return self.__rate_on

    @rate_on.setter
    def rate_on(self, rate_on: ModelParameter) -> None:
        """ Set the rate when the neuron is active. """
        self.__rate_on = rate_on

    @property
    def rate_off(self) -> ModelParameter:
        """ Get the rate when the neuron is inactive. """
        return self.__rate_off

    @rate_off.setter
    def rate_off(self, rate_off: ModelParameter) -> None:
        """ Set the rate when the neuron is inactive. """
        self.__rate_off = rate_off

    @property
    def v_init(self) -> ModelParameter:
        """ Get the initial membrane voltage. """
        return self.__v_init

    @v_init.setter
    def v_init(self, v_init: ModelParameter) -> None:
        """ Set the initial membrane voltage. """
        self.__v_init = v_init

    @property
    def v_rest(self) -> ModelParameter:
        """ Get the resting membrane voltage. """
        return self.__v_rest

    @v_rest.setter
    def v_rest(self, v_rest: ModelParameter) -> None:
        """ Set the resting membrane voltage. """
        self.__v_rest = v_rest

    @property
    def tau_m(self) -> ModelParameter:
        """ Get the membrane time constant. """
        return self.__tau_m

    @tau_m.setter
    def tau_m(self, tau_m: ModelParameter) -> None:
        """ Set the membrane time constant. """
        self.__tau_m = tau_m

    @property
    def cm(self) -> ModelParameter:
        """ Get the membrane capacitance. """
        return self.__cm

    @cm.setter
    def cm(self, cm: ModelParameter) -> None:
        """ Set the membrane capacitance. """
        self.__cm = cm

    @property
    def i_offset(self) -> ModelParameter:
        """ Get the offset current. """
        return self.__i_offset

    @i_offset.setter
    def i_offset(self, i_offset: ModelParameter) -> None:
        """ Set the offset current. """
        self.__i_offset = i_offset

    @property
    def v_reset(self) -> ModelParameter:
        """ Get the reset voltage. """
        return self.__v_reset

    @v_reset.setter
    def v_reset(self, v_reset: ModelParameter) -> None:
        """ Set the reset voltage. """
        self.__v_reset = v_reset

    @property
    def tau_refrac(self) -> ModelParameter:
        """ Get the refractory period. """
        return self.__tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac: ModelParameter) -> None:
        """ Set the refractory period. """
        self.__tau_refrac = tau_refrac

    @property
    def w_fb(self) -> ModelParameter:
        """ Get the feedback weight for the readout. """
        return self.__w_fb

    @w_fb.setter
    def w_fb(self, new_value: ModelParameter) -> None:
        """ Set the feedback weight for the readout. """
        self.__w_fb = new_value

    @property
    def window_size(self) -> ModelParameter:
        """ Get the size of the learning window. """
        return self.__window_size

    @window_size.setter
    def window_size(self, new_value: ModelParameter) -> None:
        """ Set the size of the learning window. """
        self.__window_size = new_value

    @property
    @overrides(NeuronModel.uses_eprop)
    def uses_eprop(self) -> bool:
        return True
