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
# COUNT_REFRAC = "count_refrac"
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
# ADPT = "adpt"
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

# UNITS = {
#     V: 'mV',
#     V_REST: 'mV',
#     TAU_M: 'ms',
#     CM: 'nF',
#     I_OFFSET: 'nA',
#     V_RESET: 'mV',
#     TAU_REFRAC: 'ms',
#     Z: 'N/A',
#     A: 'N/A',
#     PSI: 'N/A',
#     BIG_B: "mV",
#     SMALL_B: "mV",
#     SMALL_B_0: "mV",
#     TAU_A: "ms",
#     BETA: "N/A",
# #          ADPT: "mV"
#     SCALAR: "dimensionless"
# }


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
        # "_adpt"
        "__scalar",

        # reg params
        "__target_rate",
        "__tau_err",

        # learning signal
        "__l",
        "__w_fb",
        # "__eta",
        "__window_size",
        "__number_of_cues",

        # eprop "global"
        "__core_pop_rate",
        "__core_target_rate",
        "__rate_exp_TC",
        "__eta"
        ]

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
            # threshold params
            B,
            small_b,
            small_b_0,
            tau_a,
            beta,
            # regularisation params
            target_rate,
            tau_err,
            l,
            w_fb,
            # eta,
            window_size,
            number_of_cues,
            # eprop "global"
            eta
            ):
        # TODO: documentation

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
            (DataType.S1615, Z),  #  Z
            (DataType.S1615, A),  #  A
            (DataType.S1615, PSI),  #  psi, pseuo_derivative
            (DataType.S1615, BIG_B),
            (DataType.S1615, SMALL_B),
            (DataType.S1615, SMALL_B_0),
            (DataType.UINT32, TAU_A),
            (DataType.S1615, BETA),
            # (DataType.UINT32, ADPT),
            (DataType.S1615, SCALAR),
            (DataType.S1615, L),
            (DataType.S1615, W_FB),
            (DataType.UINT32, WINDOW_SIZE),
            (DataType.UINT32, NUMBER_OF_CUES),
            (DataType.S1615, CORE_POP_RATE), # core_pop_rate
            (DataType.S1615, TARGET_RATE),  #  core_target_rate
            (DataType.S1615, TAU_ERR),  #  rate_exp_TC
            (DataType.S1615, ETA)]    #  eta (learning rate)

        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                # eprop syn state
                [(DataType.S1615, DELTA_W+str(n)), # delta_w
                 (DataType.S1615, Z_BAR_OLD+str(n)), # z_bar_old
                 (DataType.S1615, Z_BAR+str(n)), # z_bar
                 (DataType.S1615, EP_A+str(n)), # ep_a
                 (DataType.S1615, E_BAR+str(n)), # e_bar
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
        self.__psi = psi  # calculate from v and v_thresh (but will probably end up zero)

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
        self.__l = l
        self.__w_fb = w_fb
        # self.__eta = eta
        self.__window_size = window_size
        self.__number_of_cues = number_of_cues

        # eprop "global"
        # self.__core_pop_rate = target_rate
        # self.__core_target_rate = target_rate
        # self.__rate_exp_TC = numpy.exp(-float(ts/1000)/self.__tau_err)
        self.__eta = eta

    # @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    # def get_n_cpu_cycles(self, n_neurons):
    #     # A bit of a guess
    #     return 100 * n_neurons

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
        # parameters[CORE_TARGET_RATE] = self.__core_target_rate
        # parameters[RATE_EXP_TC] = self.__rate_exp_TC
        parameters[TARGET_RATE] = self.__target_rate
        parameters[TAU_ERR] = self.__tau_err
        parameters[ETA] = self.__eta

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0
        state_variables[PSI] = self.__psi
        state_variables[Z] = 0  # initalise to zero
        state_variables[A] = 0  # initialise to zero

        state_variables[BIG_B] = self.__B
        state_variables[SMALL_B] = self.__small_b

        state_variables[L] = self.__l

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            state_variables[EP_A+str(n)] = 0
            state_variables[E_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self.__window_size

    # @overrides(AbstractNeuronModel.get_units)
    # def get_units(self, variable):
    #     return UNITS[variable]
    #
    # @overrides(AbstractNeuronModel.has_variable)
    # def has_variable(self, variable):
    #     return variable in UNITS
    #
    # @inject_items({"ts": "MachineTimeStep"})
    # @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    # def get_values(self, parameters, state_variables, vertex_slice, ts):
    #
    #     ulfract = pow(2, 32)
    #
    #     # Add the rest of the data
    #     values = [state_variables[V],
    #               parameters[V_REST],
    #             parameters[TAU_M] / parameters[CM],
    #             parameters[TAU_M].apply_operation(
    #                 operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
    #             parameters[I_OFFSET],
    #             state_variables[COUNT_REFRAC],
    #             parameters[V_RESET],
    #             parameters[TAU_REFRAC].apply_operation(
    #                 operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),
    #             state_variables[Z],
    #             state_variables[A],
    #             state_variables[PSI],
    #
    #             state_variables[BIG_B],
    #             state_variables[SMALL_B],
    #             parameters[SMALL_B_0],
    #             parameters[TAU_A].apply_operation(
    #                 operation=lambda
    #                 x: numpy.exp(float(-ts) / (1000.0 * x)) * ulfract),
    #             parameters[BETA],
    #             parameters[TAU_A].apply_operation(
    #                 operation=lambda x: (1 - numpy.exp(
    #                     float(-ts) / (1000.0 * x))) * ulfract), # ADPT
    #             parameters[SCALAR],
    #
    #             state_variables[L],
    #             parameters[W_FB],
    #             parameters[WINDOW_SIZE],
    #             parameters[NUMBER_OF_CUES]
    #             ]
    #
    #     # create synaptic state - init all state to zero
    #     for n in range(SYNAPSES_PER_NEURON):
    #         eprop_syn_init = [state_variables[DELTA_W+str(n)],
    #                           state_variables[Z_BAR_OLD+str(n)],
    #                           state_variables[Z_BAR+str(n)],
    #                           state_variables[EP_A+str(n)],
    #                           state_variables[E_BAR+str(n)],
    #                           state_variables[UPDATE_READY+str(n)]
    #                           ]
    #         # extend to appropriate fan-in
    #         values.extend(eprop_syn_init)  # * SYNAPSES_PER_NEURON)
    #
    #     return values
    #
    # @inject_items({"ts": "MachineTimeStep"})
    # @overrides(AbstractNeuronModel.get_global_values,
    #            additional_arguments={'ts'})
    # def get_global_values(self, ts):
    #     glob_vals = [
    #         self.__target_rate,     #  initialise global pop rate to the target
    #         self.__target_rate,     #  set target rate
    #         numpy.exp(-float(ts/1000)/self.__tau_err),
    #         self.__eta              # learning rate
    #         ]
    #
    #     print("\n ")
    #     print(glob_vals)
    #     print(ts)
    #     print("\n")
    #     return glob_vals
    #
    #
    # @overrides(AbstractNeuronModel.update_values)
    # def update_values(self, values, parameters, state_variables):
    #
    #     delta_w = [0] * SYNAPSES_PER_NEURON
    #     z_bar_old = [0] * SYNAPSES_PER_NEURON
    #     z_bar = [0] * SYNAPSES_PER_NEURON
    #     ep_a = [0] * SYNAPSES_PER_NEURON
    #     e_bar = [0] * SYNAPSES_PER_NEURON
    #     update_ready = [0] * SYNAPSES_PER_NEURON
    #     # Read the data
    #     (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
    #      _v_reset, _tau_refrac, psi,
    #      big_b, small_b, _small_b_0, _e_to_dt_on_tau_a, _beta, adpt, scalar,
    #      l, __w_fb, window_size, number_of_cues, delta_w, z_bar_old, z_bar, ep_a, e_bar, update_ready) = values
    #
    #     # Not sure this will work with the new array of synapse!!!
    #     # (Note that this function is only called if you do e.g. run(), set(),
    #     # run() i.e. it's not used by auto-pause and resume, so this is
    #     # untested)
    #     # todo check alignment on this
    #
    #     # Copy the changed data only
    #     state_variables[V] = v
    #     state_variables[COUNT_REFRAC] = count_refrac
    #     state_variables[PSI] = psi
    #
    #     state_variables[BIG_B] = big_b
    #     state_variables[SMALL_B] = small_b
    #
    #     state_variables[L] = l
    #
    #     for n in range(SYNAPSES_PER_NEURON):
    #         state_variables[DELTA_W+str(n)] = delta_w[n]
    #         state_variables[Z_BAR_OLD+str(n)] = z_bar_old[n]
    #         state_variables[Z_BAR+str(n)] = z_bar[n]
    #         state_variables[EP_A+str(n)] = ep_a[n]
    #         state_variables[E_BAR+str(n)] = e_bar[n]
    #         state_variables[UPDATE_READY] = update_ready[n]

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

    @window_size.setter
    def window_size(self, new_value):
        self.__number_of_cues = new_value

    # setter for "globals" like target rate etc. ?
