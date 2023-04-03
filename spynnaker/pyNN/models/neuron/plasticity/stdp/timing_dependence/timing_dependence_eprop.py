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
from spinn_utilities.overrides import overrides
# from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
#     plasticity_helpers)
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)

logger = logging.getLogger(__name__)

# LOOKUP_TAU_PLUS_SIZE = 256
# LOOKUP_TAU_PLUS_SHIFT = 0
# LOOKUP_TAU_MINUS_SIZE = 256
# LOOKUP_TAU_MINUS_SHIFT = 0


class TimingDependenceEprop(AbstractTimingDependence):
    __slots__ = [
        "__synapse_structure",
        "__a_plus",
        "__a_minus"]

    def __init__(self, A_plus=0.01, A_minus=0.01):

        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self.__synapse_structure = SynapseStructureWeightOnly()

#         # provenance data
#         self.__tau_plus_last_entry = None
#         self.__tau_minus_last_entry = None

    @property
    def A_plus(self):
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self.__a_plus = new_value

    @property
    def A_minus(self):
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self.__a_minus = new_value

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceEprop):
            return False
        return (self.__tau_plus == timing_dependence.tau_plus and
                self.__tau_minus == timing_dependence.tau_minus)

    @property
    def vertex_executable_suffix(self):
        return "eprop"

    @property
    def pre_trace_n_bytes(self):

        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 0

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales):
        # There are currently no parameters to write for this rule
        pass

        # Check timestep is valid
#         if machine_time_step != 1000:
#             raise NotImplementedError(
#                 "STDP LUT generation currently only supports 1ms timesteps")

#         # Write lookup tables
#         self.__tau_plus_last_entry = plasticity_helpers.write_exp_lut(
#             spec, self.__tau_plus, LOOKUP_TAU_PLUS_SIZE,
#             LOOKUP_TAU_PLUS_SHIFT)
#         self.__tau_minus_last_entry = plasticity_helpers.write_exp_lut(
#             spec, self.__tau_minus, LOOKUP_TAU_MINUS_SIZE,
#             LOOKUP_TAU_MINUS_SHIFT)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

#     @overrides(AbstractTimingDependence.get_provenance_data)
#     def get_provenance_data(self, pre_population_label, post_population_label):
#         prov_data = list()
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_plus_last_entry", "tau_plus", self.__tau_plus_last_entry))
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_minus_last_entry", "tau_minus", self.__tau_minus_last_entry))
#         return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return []
