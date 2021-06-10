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

import logging
from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.neuron.plasticity.stdp.common\
    import get_exp_lut_array, float_to_fixed
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightEligibilityTrace
from spinn_front_end_common.utilities.globals_variables import get_simulator

logger = logging.getLogger(__name__)

# LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
# LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0
# LOOKUP_TAU_C_SIZE = 520
LOOKUP_TAU_C_SHIFT = 4
# LOOKUP_TAU_D_SIZE = 370
LOOKUP_TAU_D_SHIFT = 2


class TimingDependenceIzhikevichNeuromodulation(AbstractTimingDependence):
    __slots__ = [
        "__synapse_structure",
        "__tau_minus",
        "__tau_minus_data",
        "__tau_plus",
        "__tau_plus_data",
        "__tau_c",
        "__tau_c_data",
        "__tau_d",
        "__tau_d_data"]

    def __init__(self, tau_plus=20.0, tau_minus=20.0, tau_c=1000, tau_d=200):
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus
        self.__tau_c = tau_c
        self.__tau_d = tau_d

        self.__synapse_structure = SynapseStructureWeightEligibilityTrace()

        ts = get_simulator().machine_time_step / 1000.0
        self.__tau_plus_data = get_exp_lut_array(
            ts, self.__tau_plus,
            shift=LOOKUP_TAU_PLUS_SHIFT)
        self.__tau_minus_data = get_exp_lut_array(
            ts, self.__tau_minus,
            shift=LOOKUP_TAU_MINUS_SHIFT)
        self.__tau_c_data = get_exp_lut_array(
            ts, self.__tau_c,
            shift=LOOKUP_TAU_C_SHIFT)
        self.__tau_d_data = get_exp_lut_array(
            ts, self.__tau_d,
            shift=LOOKUP_TAU_D_SHIFT)

    @property
    def tau_plus(self):
        return self.__tau_plus

    @property
    def tau_minus(self):
        return self.__tau_minus

    @property
    def tau_c(self):
        return self.__tau_c

    @property
    def tau_d(self):
        return self.__tau_d

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence,
                          TimingDependenceIzhikevichNeuromodulation):
            return False
        return ((self.__tau_plus == timing_dependence.tau_plus) and
                (self.__tau_minus == timing_dependence.tau_minus) and
                (self.__tau_c == timing_dependence.tau_c) and
                (self.__tau_d == timing_dependence.tau_d))

    @property
    def vertex_executable_suffix(self):
        return "izhikevich_neuromodulation"

    @property
    def pre_trace_n_bytes(self):
        # Pair rule requires no pre-synaptic trace when only the nearest
        # neighbours are considered and, a single 16-bit R1 trace
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        lut_array_words = (
            len(self.__tau_plus_data) + len(self.__tau_minus_data) +
            len(self.__tau_c_data) + len(self.__tau_d_data))
        return (lut_array_words * BYTES_PER_WORD) + 4

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, weight_scales):
        # Write lookup tables
        spec.write_array(self.__tau_plus_data)
        spec.write_array(self.__tau_minus_data)
        spec.write_array(self.__tau_c_data)
        spec.write_array(self.__tau_d_data)

        # Calculate constant component in Izhikevich's model weight update
        # function and write to SDRAM.
        weight_update_component = \
            1 / (-((1.0/self.__tau_c) + (1.0/self.__tau_d)))
        weight_update_component = float_to_fixed(weight_update_component)
        spec.write_value(data=weight_update_component,
                         data_type=DataType.INT32)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['tau_plus', 'tau_minus', 'tau_c', 'tau_d']
