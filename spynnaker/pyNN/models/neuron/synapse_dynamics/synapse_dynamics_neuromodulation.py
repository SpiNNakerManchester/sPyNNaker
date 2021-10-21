# Copyright (c) 2021 The University of Manchester
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
from pyNN.standardmodels.synapses import StaticSynapse
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    STDP_FIXED_POINT_ONE, get_exp_lut_array)
from spinn_front_end_common.utilities.globals_variables import get_simulator
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


class SynapseDynamicsNeuromodulation(AbstractPlasticSynapseDynamics):
    """ Synapses that target a neuromodulation receptor
    """

    __slots__ = [
        "__weight",
        "__tau_c",
        "__tau_d",
        "__tau_c_data",
        "__tau_d_data",
        "__w_min",
        "__w_max"]

    def __init__(self, weight=StaticSynapse.default_parameters['weight'],
                 tau_c=1000.0, tau_d=200.0, w_min=0.0, w_max=1.0):
        self.__weight = weight
        self.__tau_c = tau_c
        self.__tau_d = tau_d
        ts = get_simulator().machine_time_step / 1000.0
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
            post_vertex_slice, n_synapse_types, max_n_synapses):
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
            fp_size, fp_data):
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

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(self):
        return numpy.array([NEUROMODULATION_TARGETS["reward"]],
                           dtype=numpy.uint32)

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self):
        return 1 * BYTES_PER_WORD

    @property
    @overrides(AbstractPlasticSynapseDynamics.changes_during_run)
    def changes_during_run(self):
        return False

    @property
    @overrides(AbstractPlasticSynapseDynamics.weight)
    def weight(self):
        return self.__weight

    @property
    @overrides(AbstractPlasticSynapseDynamics.delay)
    def delay(self):
        # Delay is always 1!
        return 1

    @overrides(AbstractPlasticSynapseDynamics.set_delay)
    def set_delay(self, delay):
        if delay != 1:
            raise SynapticConfigurationException(
                "Neuromodulation delay must be 0")

    @property
    @overrides(AbstractPlasticSynapseDynamics.pad_to_length)
    def pad_to_length(self):
        return None

    @overrides(AbstractPlasticSynapseDynamics.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        return NEUROMODULATION_TARGETS.get(target, None)

    @overrides(AbstractPlasticSynapseDynamics.are_weights_signed)
    def are_weights_signed(self):
        return False
