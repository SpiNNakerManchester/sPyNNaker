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
SYNAPSES_PER_NEURON = 1024



V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"
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
W_FB = "w_fb"
WINDOW_SIZE = "window_size"
NUMBER_OF_CUES = "number_of_cues"
INPUT_SYNAPSES = "input_synapses"
REC_SYNAPSES = "rec_synapses"
NEURON_RATE = "neuron_rate"
V_MEM_LR = "v_mem_lr"
FIRING_LR = "firing_lr"

DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
EP_A = "ep_a"
E_BAR = "e_bar"
UPDATE_READY = "update_ready"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms',
    Z: 'N/A',
    A: 'N/A',
    PSI: 'N/A',
    BIG_B: "mV",
    SMALL_B: "mV",
    SMALL_B_0: "mV",
    TAU_A: "ms",
    BETA: "N/A",
    SCALAR: "dimensionless"
}


class NeuronModelEPropAdaptive(AbstractNeuronModel):
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
        "__l",
        "__w_fb",
        "__eta",
        "__window_size",
        "__number_of_cues",
        "__input_synapses",
        "__rec_synapses",
        "__neuron_rate",
        "__v_mem_lr",
        "__firing_lr"
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
            scalar,

            # regularisation params
            target_rate,
            tau_err,
            l,
            eta,
            window_size,
            number_of_cues,
            input_synapses,
            rec_synapses,
            neuron_rate,
            v_mem_lr,
            firing_lr,
            w_fb
            ):

        datatype_list = [
            # neuron params
            DataType.S1615,   #  v
            DataType.S1615,   #  v_rest
            DataType.S1615,   #  r_membrane (= tau_m / cm)
            DataType.S1615,   #  exp_tc (= e^(-ts / tau_m))
            DataType.S1615,   #  i_offset
            DataType.INT32,   #  count_refrac
            DataType.S1615,   #  v_reset
            DataType.INT32,   #  tau_refrac
            DataType.S1615,   #  Z
            DataType.S1615,   #  A
            DataType.S1615,   #  psi, pseuo_derivative
            # threshold params
            DataType.S1615,   # B
            DataType.S1615,   # b
            DataType.S1615,   # b_0
            DataType.UINT32,    # tau_a (apply operation to input val giving UFRACT)
            DataType.S1615,   # beta
            DataType.UINT32,    # adpt (apply operation to input val giving UFRACT)
            DataType.S1615,   # scalar
            # Learning signal
            DataType.S1615,   #  L
            DataType.UINT32,   #  window_size
            DataType.UINT32,   #  number_of_cues
            DataType.UINT32,   #  input_synapses
            DataType.UINT32,   #  rec_synapses
            DataType.S1615,   #  neuron_rate
            DataType.S1615,   #  v_mem_lr
            DataType.S1615,   #  firing_lr
            # DataType.S1615,   #  w_fb
            ]
        datatype_list.extend([DataType.S1615] * 20)  # w_fb

        # Synapse states - always initialise to zero
        eprop_syn_state = [ # synaptic state, one per synapse (kept in DTCM)
                DataType.S1615, # delta_w
                DataType.S1615, # z_bar_old
                DataType.S1615, # z_bar
                DataType.S1615, # ep_a
                DataType.S1615, # e_bar
                DataType.INT32 # update_ready
            ]
        # Extend to include fan-in for each neuron
        datatype_list.extend(eprop_syn_state * SYNAPSES_PER_NEURON)

        global_data_types = [
            DataType.S1615,   #  core_pop_rate
            DataType.S1615,   #  core_target_rate
            DataType.S1615,   #  rate_exp_TC
            DataType.S1615    #  eta (learning rate)
            ]

        super(NeuronModelEPropAdaptive, self).__init__(data_types=datatype_list,
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
        self.__psi = psi  # calculate from v and v_thresh (but will probably end up zero)

        # threshold params
        self.__B = B
        self.__small_b = small_b
        self.__small_b_0 = small_b_0
        self.__tau_a = tau_a
        self.__beta = beta
        self.__scalar = scalar

        # Regularisation params
        self.__target_rate = target_rate
        self.__tau_err = tau_err

        # learning signal
        self.__l = l
        self.__w_fb = w_fb
        self.__eta = eta
        self.__window_size = window_size
        self.__number_of_cues = number_of_cues
        self.__input_synapses = input_synapses
        self.__rec_synapses = rec_synapses
        self.__neuron_rate = self.__target_rate
        self.__v_mem_lr = v_mem_lr
        self.__firing_lr = firing_lr


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

        parameters[SMALL_B_0] = self.__small_b_0
        parameters[TAU_A] = self.__tau_a
        parameters[BETA] = self.__beta
        parameters[SCALAR] = self.__scalar
        parameters[WINDOW_SIZE] = self.__window_size
        parameters[NUMBER_OF_CUES] = self.__number_of_cues
        parameters[INPUT_SYNAPSES] = self.__input_synapses
        parameters[REC_SYNAPSES] = self.__rec_synapses
        parameters[NEURON_RATE] = self.__neuron_rate
        parameters[V_MEM_LR] = self.__v_mem_lr
        parameters[FIRING_LR] = self.__firing_lr
#         print('w_fb: ', self.__w_fb)
        for n in range(20):
            parameters[W_FB+str(n)] = self.__w_fb[n]#.next()


    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[COUNT_REFRAC] = 0
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

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        ulfract = pow(2, 32)

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
                state_variables[Z],
                state_variables[A],
                state_variables[PSI],

                state_variables[BIG_B],
                state_variables[SMALL_B],
                parameters[SMALL_B_0],
                parameters[TAU_A].apply_operation(
                    operation=lambda
                    x: numpy.exp(float(-ts) / (1000.0 * x)) * ulfract), # TAU_A
                parameters[BETA],
                parameters[TAU_A].apply_operation(
                    operation=lambda x: (1 - numpy.exp(
                        float(-ts) / (1000.0 * x))) * ulfract), # ADPT
                parameters[SCALAR],

                state_variables[L],
                parameters[WINDOW_SIZE],
                parameters[NUMBER_OF_CUES],
                parameters[INPUT_SYNAPSES],
                parameters[REC_SYNAPSES],
                parameters[NEURON_RATE],
                parameters[V_MEM_LR],
                parameters[FIRING_LR]
                ]
        for n in range(20):
            feedback_weight = [parameters[W_FB+str(n)]]
            values.extend(feedback_weight)

        # create synaptic state - init all state to zero
        for n in range(SYNAPSES_PER_NEURON):
            eprop_syn_init = [state_variables[DELTA_W+str(n)],
                              state_variables[Z_BAR_OLD+str(n)],
                              state_variables[Z_BAR+str(n)],
                              state_variables[EP_A+str(n)],
                              state_variables[E_BAR+str(n)],
                              state_variables[UPDATE_READY+str(n)]
                              ]
            # extend to appropriate fan-in
            values.extend(eprop_syn_init)  # * SYNAPSES_PER_NEURON)

        return values

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'ts'})
    def get_global_values(self, ts):
        glob_vals = [
            self.__target_rate,     #  initialise global pop rate to the target
            self.__target_rate,     #  set target rate
            numpy.exp(-float(ts/1000)/self.__tau_err),
            self.__eta              # learning rate
            ]

        # print("\n ")
        # print(glob_vals)
        # print(ts)
        # print("\n")
        return glob_vals


    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        delta_w = [0] * SYNAPSES_PER_NEURON
        z_bar_old = [0] * SYNAPSES_PER_NEURON
        z_bar = [0] * SYNAPSES_PER_NEURON
        ep_a = [0] * SYNAPSES_PER_NEURON
        e_bar = [0] * SYNAPSES_PER_NEURON
        update_ready = [0] * SYNAPSES_PER_NEURON
        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac, psi,
         big_b, small_b, _small_b_0, _e_to_dt_on_tau_a, _beta, _adpt, _scalar,
         l, __w_fb, window_size, number_of_cues, input_synapses, rec_synapses, neuron_rate, v_mem_lr, firing_lr,
         delta_w, z_bar_old, z_bar, ep_a, e_bar, update_ready) = values

        # Not sure this will work with the new array of synapse!!!
        # (Note that this function is only called if you do e.g. run(), set(),
        # run() i.e. it's not used by auto-pause and resume, so this is
        # untested)
        # todo check alignment on this

        # Copy the changed data only
        state_variables[V] = v
        state_variables[COUNT_REFRAC] = count_refrac
        state_variables[PSI] = psi

        state_variables[BIG_B] = big_b
        state_variables[SMALL_B] = small_b

        state_variables[L] = l

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = delta_w[n]
            state_variables[Z_BAR_OLD+str(n)] = z_bar_old[n]
            state_variables[Z_BAR+str(n)] = z_bar[n]
            state_variables[EP_A+str(n)] = ep_a[n]
            state_variables[E_BAR+str(n)] = e_bar[n]
            state_variables[UPDATE_READY] = update_ready[n]


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

    @property
    def input_synapses(self):
        return self.__input_synapses

    @input_synapses.setter
    def input_synapses(self, new_value):
        self.__input_synapses = new_value

    @property
    def rec_synapses(self):
        return self.__rec_synapses

    @rec_synapses.setter
    def rec_synapses(self, new_value):
        self.__rec_synapses = new_value

    @property
    def neuron_rate(self):
        return self.__neuron_rate

    @neuron_rate.setter
    def neuron_rate(self, new_value):
        self.__neuron_rate = new_value

    @property
    def v_mem_lr(self):
        return self.__v_mem_lr

    @v_mem_lr.setter
    def v_mem_lr(self, new_value):
        self.__v_mem_lr = new_value

    @property
    def firing_lr(self):
        return self.__firing_lr

    @firing_lr.setter
    def firing_lr(self, new_value):
        self.__firing_lr = new_value
