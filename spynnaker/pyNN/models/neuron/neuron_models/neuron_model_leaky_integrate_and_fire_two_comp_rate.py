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
from setuptools.dist import assert_string_list

MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0

U = "u"
U_REST = "u_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"

V = "v"
V_STAR = "v_star"
TAU_L = "tau_L"
G_D = "g_D"
G_L = "g_L"

MEAN_ISI_TICKS = "mean_isi_ticks"
TIME_TO_SPIKE_TICKS = "time_to_spike_ticks"
SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"
SEED4 = "seed4"
TICKS_PER_SECOND = "ticks_per_second"
TIME_SINCE_LAST_SPIKE = "time_since_last_spike"
RATE_AT_LAST_SETTING = "rate_at_last_setting"
RATE_UPDATE_THRESHOLD = "rate_update_threshold"
RATE_DIFF = "rate_diff"

UNITS = {
    U: 'mV',
    U_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms'
}


class NeuronModelLeakyIntegrateAndFireTwoCompRate(AbstractNeuronModel):
    __slots__ = [
        "__u_init",
        "__u_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",

        "__g_L",
        "__g_D",
        "__tau_L",
        "__v",
        "__v_star",

        "__mean_isi_ticks",
        "__time_to_spike_ticks",
        "__time_since_last_spike",
        "__rate_at_last_setting",
        "__rate_update_threshold",
        "__rate_diff",
        "__target_data"
        ]

    def __init__(
            self, u_init, u_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            g_D, g_L, tau_L, v_init, v_star,
            mean_isi_ticks, time_to_spike_ticks, rate_update_threshold, starting_rate):

        global_data_types=[
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.S1615,    # ticks_per_second
                    ]

        super(NeuronModelLeakyIntegrateAndFireTwoCompRate, self).__init__(
            data_types = [DataType.S1615,   # v
                DataType.S1615,   # v_rest
                DataType.S1615,   # r_membrane (= tau_m / cm)
                DataType.S1615,   # exp_tc (= e^(-ts / tau_m))
                DataType.S1615,   # i_offset
                DataType.INT32,   # count_refrac
                DataType.S1615,   # v_reset
                DataType.INT32,   # tau_refrac

                DataType.S1615,   # V
                DataType.S1615,   # V*
                DataType.S1615,   # g_D/(g_D +g_L)
                DataType.S1615,   # exp_tc_dend (= e^(-ts / tau_m))

                #### Poisson Compartment Params ####
                DataType.S1615,   #  REAL mean_isi_ticks
                DataType.S1615,   #  REAL time_to_spike_ticks
                DataType.INT32,    #  int32_t time_since_last_spike s
                DataType.S1615,   #  REAL rate_at_last_setting; s
                DataType.S1615,   #  REAL rate_update_threshold; p
                DataType.S1615    #  REAL rate difference
                ],
            global_data_types=global_data_types)

        if u_init is None:
            u_init = v_rest
        self.__u_init = u_init
        self.__u_rest = u_rest
        self.__tau_m = (1/(g_L + g_D))
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac

        self.__g_L = g_L
        self.__g_D = g_D
        self.__tau_L = tau_L

        self.__mean_isi_ticks = mean_isi_ticks
        self.__time_to_spike_ticks = time_to_spike_ticks
        self.__time_since_last_spike = 0 # this should be initialised to zero - we know nothing about before the simulation
        self.__rate_at_last_setting = starting_rate
        self.__rate_update_threshold = 2
        self.__rate_diff = 0 # same as sime_since last spike

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[U_REST] = self.__u_rest
        parameters[TAU_M] = 1 / (self.__g_L + self.__g_D)  # self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac

        parameters[TAU_L] = self.__tau_L
        parameters[G_D] = self.__g_D
        parameters[G_L] = self.__g_L

        parameters[TICKS_PER_SECOND] = 0 # set in get_valuers()
        parameters[RATE_UPDATE_THRESHOLD] = self.__rate_update_threshold

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[U] = self.__u_init
        state_variables[COUNT_REFRAC] = 0

        state_variables[V] = self.__u_init # initialise to soma potential
        state_variables[V_STAR] = self.__u_init # initialise to soma potential


        state_variables[MEAN_ISI_TICKS] = self.__mean_isi_ticks
        state_variables[TIME_TO_SPIKE_TICKS] = self.__time_to_spike_ticks # could eventually be set from membrane potential
        state_variables[TIME_SINCE_LAST_SPIKE] = self.__time_since_last_spike
        state_variables[RATE_AT_LAST_SETTING] = self.__rate_at_last_setting
        state_variables[RATE_DIFF] = self.__rate_diff

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
        return [state_variables[U],
                parameters[U_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),


                state_variables[V],
                state_variables[V_STAR],
                parameters[CM]/(parameters[G_D] + parameters[G_L]),
                parameters[TAU_L].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),


                state_variables[MEAN_ISI_TICKS],
                state_variables[TIME_TO_SPIKE_TICKS],
                state_variables[TIME_SINCE_LAST_SPIKE],
                state_variables[RATE_AT_LAST_SETTING],
                parameters[RATE_UPDATE_THRESHOLD],
                state_variables[RATE_DIFF]
                ]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (u, _u_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac,
         v, v_star, _v_star_cond, _exp_tc_den,
         mean_isi_ticks, time_to_spike_ticks,
         time_since_last_spike, rate_at_last_setting, _rate_update_threshold,
         rate_diff
         ) = values

        # Copy the changed data only
        state_variables[U] = u
        state_variables[COUNT_REFRAC] = count_refrac

        state_variables[V] = v
        state_variables[V_INIT] = v_star

        state_variables[MEAN_ISI_TICKS] = mean_isi_ticks
        state_variables[TIME_TO_SPIKE_TICKS] = time_to_spike_ticks
        state_variables[TIME_SINCE_LAST_SPIKE] = time_since_last_spike
        state_variables[RATE_AT_LAST_SETTING] = rate_at_last_setting
        state_variables[RATE_DIFF] = rate_diff

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'machine_time_step'})
    def get_global_values(self, machine_time_step):
        vals = [
                1, # seed 1
                2, # seed 2
                3, # seed 3
                4, # seed 4
                MICROSECONDS_PER_SECOND / float(machine_time_step) # ticks_per_second
                ]

        return vals


    @property
    def u_init(self):
        return self.__u_init

    @u_init.setter
    def u_init(self, u_init):
        self.__u_init = u_init

    @property
    def u_rest(self):
        return self.__u_rest

    @u_rest.setter
    def u_rest(self, u_rest):
        self.__u_rest = u_rest

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
    def mean_isi_ticks(self):
        return self.__mean_isi_ticks

    @mean_isi_ticks.setter
    def mean_isi_ticks(self, new_mean_isi_ticks):
        self.__mean_isi_ticks = new_mean_isi_ticks

    @property
    def time_to_spike_ticks(self):
        return self.__time_to_spike_ticks

    @mean_isi_ticks.setter
    def time_to_spike_ticks(self, new_time_to_spike_ticks):
        self.__time_to_spike_ticks = new_time_to_spike_ticks
