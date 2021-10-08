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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    STDP_FIXED_POINT_ONE)

# The targets of neuromodulation
NEUROMODULATION_TARGETS = {
    "reward": 0,
    "punishment": 1
}


class SynapseDynamicsNeuromodulation(AbstractPlasticSynapseDynamics):
    """ Synapses that target a neuromodulation receptor
    """

    def __init__(self, weight=StaticSynapse.default_parameters['weight']):
        self.__weight = weight

    @overrides(AbstractPlasticSynapseDynamics.merge)
    def merge(self, synapse_dynamics):
        # If dynamics is STDP, check neuromodulation
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            if not synapse_dynamics.neuromodulation:
                raise SynapticConfigurationException(
                    "An existing edge has been added with STDP but without "
                    "neuromodulation")
            return synapse_dynamics

        # Only other options are another neuromodulation or static, so return
        # self to override
        return self

    @overrides(AbstractPlasticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics):
        # Shouln't ever come up, but if it does, it is False!
        return False

    @overrides(AbstractPlasticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        # Shouldn't ever come up, as should be replaced by STDP
        raise NotImplementedError()

    @overrides(AbstractPlasticSynapseDynamics
               .get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        # Shouldn't ever come up, as should be replaced by STDP
        raise NotImplementedError()

    @overrides(AbstractPlasticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec, region, global_weight_scale, synapse_weight_scales):
        # Shouldn't ever come up, as should be replaced by STDP
        raise NotImplementedError()

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
        if connections:
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
