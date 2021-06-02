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
from spynnaker.pyNN.models.neural_properties import AbstractIsRateBased
import math

MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0
LUT_SIZE = 64

U = "u"
U_REST = "u_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"

Va = "v_A"
Vb = "v_B"
V_STAR = "v_star"
TAU_L = "tau_L"
G_A = "g_A"
G_B = "g_B"
G_L = "g_L"


SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"
SEED4 = "seed4"
TICKS_PER_SECOND = "ticks_per_second"
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


class NeuronModelPyramidalRate(AbstractNeuronModel, AbstractIsRateBased):
    __slots__ = [
        "__u_init",
        "__u_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",

        "__g_L",
        "__g_A",
        "__g_B",
        "__tau_L",
        "__v_A",
        "__v_B",
        "__v_star",

        "__rate_at_last_setting",
        "__rate_update_threshold",
        "__rate_diff",
        "__target_data"
        ]

    def __init__(
            self, u_init, u_rest, cm, i_offset, v_reset, v_A, v_B, g_A,
            g_B, g_L, tau_L, v_init, rate_update_threshold, starting_rate):

        global_data_types=[
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.S1615,    # ticks_per_second
                    ]

        super(NeuronModelPyramidalRate, self).__init__(
            data_types = [DataType.S1615,   # U
                DataType.S1615,   # u_rest
                DataType.S1615,   # r_membrane (= tau_m / cm)
                DataType.S1615,   # i_offset
                DataType.S1615,   # u_reset

                DataType.S1615,   # v_A
                DataType.S1615,   # V_B
                DataType.S1615,   # V*
                DataType.S1615,   # g_B / (g_A + g_B + g_L), plasticity rate multiplier

                DataType.S1615,   # g_L
                DataType.S1615,   # tau_L
                DataType.S1615,   # g_A
                DataType.S1615,   # g_B

                DataType.S1615,   # REAL rate_at_last_setting
                DataType.S1615,   # REAL rate_update_threshold
                DataType.S1615    # REAL rate difference
                ],
            global_data_types=global_data_types)

        if u_init is None:
            u_init = u_rest
        self.__u_init = u_init
        self.__u_rest = u_rest
        self.__tau_m = (1/(g_L + g_A + g_B))
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset

        self.__g_L = g_L
        self.__g_A = g_A
        self.__g_B = g_B
        self.__tau_L = tau_L
        self.__v_A = v_A
        self.__v_B = v_B

        self.__rate_at_last_setting = starting_rate
        self.__rate_update_threshold = rate_update_threshold
        self.__rate_diff = 0

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[U_REST] = self.__u_rest
        parameters[TAU_M] = 1 / (self.__g_L + self.__g_A + self.__g_B)  # self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset

        parameters[TAU_L] = self.__tau_L
        parameters[G_A] = self.__g_A
        parameters[G_B] = self.__g_B
        parameters[G_L] = self.__g_L

        parameters[TICKS_PER_SECOND] = 0 # set in get_valuers()
        parameters[RATE_UPDATE_THRESHOLD] = self.__rate_update_threshold

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[U] = self.__u_init

        state_variables[Va] = self.__v_A
        state_variables[Vb] = self.__v_B
        state_variables[V_STAR] = self.__u_init  # initialise to soma potential

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
                parameters[I_OFFSET],
                parameters[V_RESET],


                state_variables[Va],
                state_variables[Vb],
                state_variables[V_STAR],
                parameters[G_B] / (parameters[G_A] + parameters[G_B] + parameters[G_L]),

                parameters[G_L],
                parameters[TAU_L],
                parameters[G_A],
                parameters[G_B],

                state_variables[RATE_AT_LAST_SETTING],
                parameters[RATE_UPDATE_THRESHOLD],
                state_variables[RATE_DIFF]
                ]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (u, _u_rest, _r_membrane, _i_offset,
         _v_reset, v_A, v_B, v_star, _v_star_cond,
         rate_at_last_setting, _rate_update_threshold,
         rate_diff
         ) = values

        # Copy the changed data only
        state_variables[U] = u

        state_variables[Va] = v_A
        state_variables[Vb] = v_B
        # state_variables[V_INIT] = v_star

        state_variables[RATE_AT_LAST_SETTING] = rate_at_last_setting
        state_variables[RATE_DIFF] = rate_diff

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'machine_time_step'})
    def get_global_values(self, machine_time_step):
        vals = [
                1,  # seed 1
                2,  # seed 2
                3,  # seed 3
                4,  # seed 4
                MICROSECONDS_PER_SECOND / float(machine_time_step) # ticks_per_second
                ]

        return vals

    def get_rate_lut(self):

        max_rate = 150
        k = 0.5
        beta = 5
        delta = 1

        x_vals = [0.0625 * i for i in range(LUT_SIZE)]
        y_vals = [float(max_rate)/(1 + k * math.exp(beta * (delta - x))) for x in x_vals]

        return y_vals

    def get_rate_lut_size(self):
        return LUT_SIZE

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

