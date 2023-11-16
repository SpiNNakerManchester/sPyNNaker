# Copyright (c) 2021 The University of Manchester
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
import numpy
from pyNN.standardmodels.synapses import StaticSynapse
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import (
    SynapticConfigurationException, InvalidParameterType)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    STDP_FIXED_POINT_ONE, get_exp_lut_array)
from spynnaker.pyNN.types import Weight_Delay_In_Types as _Weight
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)

# The targets of neuromodulation
NEUROMODULATION_TARGETS = {
    "reward": 0,
    "punishment": 1
}

# LOOKUP_TAU_C_SIZE = 520
LOOKUP_TAU_C_SHIFT = 4
# LOOKUP_TAU_D_SIZE = 370
LOOKUP_TAU_D_SHIFT = 2


class SynapseDynamicsNeuromodulation(
        AbstractPlasticSynapseDynamics, AbstractGenerateOnMachine):
    """
    Synapses that target a neuromodulation receptor.
    """

    __slots__ = [
        "__tau_c",
        "__tau_d",
        "__tau_c_data",
        "__tau_d_data",
        "__w_min",
        "__w_max"]

    def __init__(self,
                 weight: _Weight = StaticSynapse.default_parameters['weight'],
                 tau_c=1000.0, tau_d=200.0, w_min=0.0, w_max=1.0):
        super().__init__(delay=1, weight=weight)
        self.__tau_c = tau_c
        self.__tau_d = tau_d
        ts = SpynnakerDataView.get_simulation_time_step_ms()
        self.__tau_c_data = get_exp_lut_array(
            ts, self.__tau_c, shift=LOOKUP_TAU_C_SHIFT)
        self.__tau_d_data = get_exp_lut_array(
            ts, self.__tau_d, shift=LOOKUP_TAU_D_SHIFT)
        self.__w_min = w_min
        self.__w_max = w_max

        if w_min < 0 or w_max < 0:
            raise SynapticConfigurationException(
                "Minimum and maximum weights must be >= 0")

    @property
    def tau_c(self):
        return self.__tau_c

    @property
    def tau_d(self):
        return self.__tau_d

    @property
    def w_min(self):
        return self.__w_min

    @property
    def w_max(self):
        return self.__w_max

    @overrides(AbstractPlasticSynapseDynamics.merge)
    def merge(self, synapse_dynamics):
        # This must replace something that supports neuromodulation,
        # so it can't be the first thing to be merged!
        raise SynapticConfigurationException(
            "Neuromodulation synapses can only be added where an existing"
            " projection has already been added which supports"
            " neuromodulation")

    @overrides(AbstractPlasticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics):
        # Shouln't ever come up, but if it does, it is False!
        return False

    def is_neuromodulation_same_as(self, other):
        return (self.__tau_c == other.tau_c and self.__tau_d == other.tau_d and
                self.__w_min == other.w_min and self.__w_max == other.w_max)

    @overrides(AbstractPlasticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return "izhikevich_neuromodulation_"

    @overrides(AbstractPlasticSynapseDynamics
               .get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        size = BYTES_PER_WORD * 3
        size += BYTES_PER_WORD * len(self.__tau_c_data)
        size += BYTES_PER_WORD * len(self.__tau_d_data)
        return size

    @overrides(AbstractPlasticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec, region, global_weight_scale, synapse_weight_scales):
        # Calculate constant component in Izhikevich's model weight update
        # function and write to SDRAM.
        weight_update_component = \
            1 / (-((1.0/self.__tau_c) + (1.0/self.__tau_d)))
        spec.write_value(data=weight_update_component,
                         data_type=DataType.S1615)

        # Write min and max weight
        spec.write_value(data=self.__w_max * global_weight_scale,
                         data_type=DataType.S1615)
        spec.write_value(data=self.__w_min * global_weight_scale,
                         data_type=DataType.S1615)

        # Write the LUT arrays
        spec.write_array(self.__tau_c_data)
        spec.write_array(self.__tau_d_data)

    @overrides(AbstractPlasticSynapseDynamics.get_value)
    def get_value(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @overrides(AbstractPlasticSynapseDynamics.set_value)
    def set_value(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @overrides(AbstractPlasticSynapseDynamics
               .get_n_words_for_plastic_connections)
    def get_n_words_for_plastic_connections(self, n_connections):
        # 1 for flags
        pp_size_words = 1
        # 1 or each connection
        fp_size_words = n_connections
        return pp_size_words + fp_size_words

    @overrides(AbstractPlasticSynapseDynamics.get_plastic_synaptic_data)
    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types, max_n_synapses,
            max_atoms_per_core):
        # pylint: disable=too-many-arguments
        weights = numpy.rint(
            numpy.abs(connections["weight"]) * STDP_FIXED_POINT_ONE)
        fixed_plastic = (
            ((weights.astype("uint32") & 0xFFFF) << 16) |
            ((connections["target"] - post_vertex_slice.lo_atom)) & 0xFFFF)
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype="uint8").reshape((-1, BYTES_PER_WORD)),
            max_n_synapses)

        # It is assumed that all connections have the same synapse type
        is_reward = 0
        synapse_type = 0
        if len(connections) > 0:
            synapse_type = connections[0]["synapse_type"]
            is_reward = synapse_type == NEUROMODULATION_TARGETS["reward"]
        flags = 0x80000000 | (int(is_reward) << 30) | synapse_type

        fp_size = self.get_n_items(fixed_plastic_rows, BYTES_PER_WORD)
        fp_data = [
            fixed_row.view("uint32") for fixed_row in fixed_plastic_rows]
        pp_data = [numpy.array([flags], dtype="uint32") for _ in range(n_rows)]
        pp_size = [numpy.array([1], dtype="uint32") for _ in range(n_rows)]

        return fp_data, pp_data, fp_size, pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_plastic_plastic_words_per_row)
    def get_n_plastic_plastic_words_per_row(self, pp_size):
        # pp_size is in words, so just return
        return pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_fixed_plastic_words_per_row)
    def get_n_fixed_plastic_words_per_row(self, fp_size):
        # fp_size is in words, so just return
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, pp_size, fp_size):
        # Each fixed-plastic synapse is a word and fp_size is in words so just
        # return it
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.read_plastic_synaptic_data)
    def read_plastic_synaptic_data(
            self, post_vertex_slice, n_synapse_types, pp_size, pp_data,
            fp_size, fp_data, max_atoms_per_core):
        data = numpy.concatenate(fp_data)
        connections = numpy.zeros(data.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = (data & 0xFFFF) + post_vertex_slice.lo_atom
        connections["weight"] = (data >> 16) & 0xFFFF
        connections["delay"] = 1
        return connections

    @overrides(AbstractPlasticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self):
        names = ['weight']
        return names

    @overrides(AbstractPlasticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words):
        # One word is static, the rest is for synapses
        return n_words - 1

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self):
        return MatrixGeneratorID.NEUROMODULATION_MATRIX.value

    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(
            self, synaptic_matrix_offset, delayed_matrix_offset, app_edge,
            synapse_info, max_row_info, max_pre_atoms_per_core,
            max_post_atoms_per_core):
        # pylint: disable=unused-argument
        synapse_type = synapse_info.synapse_type
        return numpy.array([
            synaptic_matrix_offset, max_row_info.undelayed_max_words,
            max_row_info.undelayed_max_n_synapses, app_edge.pre_vertex.n_atoms,
            synapse_type is NEUROMODULATION_TARGETS["reward"], synapse_type],
            dtype=numpy.uint32)

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self):
        return 6 * BYTES_PER_WORD

    @property
    @overrides(AbstractPlasticSynapseDynamics.changes_during_run)
    def changes_during_run(self):
        return False

    @property
    @overrides(AbstractPlasticSynapseDynamics.pad_to_length)
    def pad_to_length(self):
        return None

    @overrides(AbstractPlasticSynapseDynamics.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        return NEUROMODULATION_TARGETS.get(target, None)

    @property
    @overrides(AbstractPlasticSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self):
        return False
