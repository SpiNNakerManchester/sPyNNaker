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

from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_threshold_type import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct

# import numpy

BIG_B = "big_b"
SMALL_B = "small_b"
SMALL_B_0 = "small_b_0"
TAU_A = "tau_a"
BETA = "beta"
ADPT = "adpt"
SCALAR = "scalar"


class ThresholdTypeAdaptive(AbstractThresholdType):
    """ A threshold that is a static value
    """
    __slots__ = [
        "__B",
        "__small_b",
        "__small_b_0",
        "__tau_a",
        "__beta",
#         "_adpt"
        "__scalar"
        ]

    def __init__(self,  B, small_b, small_b_0, tau_a, beta):
        super().__init__(
            [Struct([
                (DataType.S1615, BIG_B),
                (DataType.S1615, SMALL_B),
                (DataType.S1615, SMALL_B_0),
                (DataType.UINT32, TAU_A),
                (DataType.S1615, BETA),
                (DataType.UINT32, SCALAR),
                (DataType.S1615, TIMESTEP_MS)])],
            {BIG_B: "mV", SMALL_B: "mV", SMALL_B_0: "mV", TAU_A: "ms", BETA: "",
             SCALAR: ""})
        self._B = B
        self._small_b = small_b
        self._small_b_0 = small_b_0
        self._tau_a = tau_a
        self._beta = beta
        self._scalar = 1000

    # @overrides(AbstractThresholdType.get_n_cpu_cycles)
    # def get_n_cpu_cycles(self, n_neurons):
    #     # Just a comparison, but 2 just in case!
    #     return 2 * n_neurons

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[SMALL_B_0] = self._small_b_0
        parameters[TAU_A] = self._tau_a
        parameters[BETA] = self._beta
        parameters[SCALAR] = self._scalar

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[BIG_B] = self._B
        state_variables[SMALL_B] = self._small_b

    # @overrides(AbstractThresholdType.get_units)
    # def get_units(self, variable):
    #     return UNITS[variable]
    #
    # @overrides(AbstractThresholdType.has_variable)
    # def has_variable(self, variable):
    #     return variable in UNITS
    #
    # @inject_items({"ts": "MachineTimeStep"})
    # @overrides(AbstractThresholdType.get_values, additional_arguments={'ts'})
    # def get_values(self, parameters, state_variables, vertex_slice, ts):
    #
    #     ulfract = pow(2, 32)
    #
    #     # Add the rest of the data
    #     return [
    #         state_variables[BIG_B],
    #         state_variables[SMALL_B],
    #         parameters[SMALL_B_0],
    #         parameters[TAU_A].apply_operation(
    #                 operation=lambda
    #                 x: numpy.exp(float(-ts) / (1000.0 * x)) * ulfract),
    #         parameters[BETA],
    #         parameters[TAU_A].apply_operation(
    #             operation=lambda x: (1 - numpy.exp(
    #             float(-ts) / (1000.0 * x))) * ulfract), # ADPT
    #         parameters[SCALAR]
    #         ]
    #
    # @overrides(AbstractThresholdType.update_values)
    # def update_values(self, values, parameters, state_variables):
    #
    #     # Read the data
    #     (big_b, small_b, _small_b_0, _e_to_dt_on_tau_a, _beta, adpt, scalar) = values
    #
    #     state_variables[BIG_B] = big_b
    #     state_variables[SMALL_B] = small_b

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, new_value):
        self._B = new_value

    @property
    def small_b(self):
        return self._small_b

    @small_b.setter
    def small_b(self, new_value):
        self._small_b = new_value

    @property
    def small_b_0(self):
        return self._small_b_0

    @small_b_0.setter
    def small_b_0(self, new_value):
        self._small_b_0 = new_value

    @property
    def tau_a(self):
        return self._tau_a

    @tau_a.setter
    def tau_a(self, new_value):
        self._tau_a = new_value

    @property
    def beta(self):
        return self._beta

    @beta.setter
    def beta(self, new_value):
        self._beta = new_value
