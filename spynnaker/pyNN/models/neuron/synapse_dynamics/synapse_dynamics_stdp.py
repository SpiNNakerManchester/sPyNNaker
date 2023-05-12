# Copyright (c) 2015 The University of Manchester
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

import math
import numpy
from pyNN.standardmodels.synapses import StaticSynapse
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import (
    SynapticConfigurationException, InvalidParameterType)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)
from .synapse_dynamics_neuromodulation import SynapseDynamicsNeuromodulation

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = BYTES_PER_WORD

# The targets of neuromodulation
NEUROMODULATION_TARGETS = {
    "reward": 0,
    "punishment": 1
}


class SynapseDynamicsSTDP(
        AbstractPlasticSynapseDynamics,
        AbstractGenerateOnMachine):
    """
    The dynamics of a synapse that changes over time using a
    Spike Timing Dependent Plasticity (STDP) rule.
    """

    __slots__ = [
        # Fraction of delay that is dendritic (instead of axonal or synaptic)
        "__dendritic_delay_fraction",
        # timing dependence to use for the STDP rule
        "__timing_dependence",
        # weight dependence to use for the STDP rule
        "__weight_dependence",
        # The neuromodulation instance if enabled
        "__neuromodulation",
        # padding to add to a synaptic row for synaptic rewiring
        "__pad_to_length",
        # Weight of connections formed by connector
        "__weight",
        # Delay of connections formed by connector
        "__delay",
        # Whether to use back-propagation delay or not
        "__backprop_delay"]

    def __init__(
            self, timing_dependence, weight_dependence,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            weight=StaticSynapse.default_parameters['weight'],
            delay=None, pad_to_length=None, backprop_delay=True):
        """
        :param AbstractTimingDependence timing_dependence:
        :param AbstractWeightDependence weight_dependence:
        :param None voltage_dependence: not supported
        :param float dendritic_delay_fraction: must be 1.0!
        :param float weight:
        :param delay: Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        :param pad_to_length:
        :type pad_to_length: int or None
        :param bool backprop_delay:
        """
        if timing_dependence is None or weight_dependence is None:
            raise NotImplementedError(
                "Both timing_dependence and weight_dependence must be"
                "specified")
        if voltage_dependence is not None:
            raise NotImplementedError(
                "Voltage dependence has not been implemented")

        self.__timing_dependence = timing_dependence
        self.__weight_dependence = weight_dependence
        # move data from timing to weight dependence; that's where we need it
        weight_dependence.set_a_plus_a_minus(
            timing_dependence.A_plus, timing_dependence.A_minus)
        self.__dendritic_delay_fraction = float(dendritic_delay_fraction)
        self.__pad_to_length = pad_to_length
        self.__weight = weight
        if delay is None:
            delay = SpynnakerDataView.get_min_delay()
        self.__delay = self._round_delay(delay)
        self.__backprop_delay = backprop_delay
        self.__neuromodulation = None

        if self.__dendritic_delay_fraction != 1.0:
            raise NotImplementedError("All delays must be dendritic!")

    def merge_neuromodulation(self, neuromodulation):
        if self.__neuromodulation is None:
            self.__neuromodulation = neuromodulation
        elif not self.__neuromodulation.is_neuromodulation_same_as(
                neuromodulation):
            raise SynapticConfigurationException(
                "Neuromodulation must match exactly when using multiple"
                " edges to the same Population")

    @overrides(AbstractPlasticSynapseDynamics.merge)
    def merge(self, synapse_dynamics):
        # If dynamics is Neuromodulation, merge with other neuromodulation,
        # and then return ourselves, as neuromodulation can't be used by
        # itself
        if isinstance(synapse_dynamics, SynapseDynamicsNeuromodulation):
            self.merge_neuromodulation(synapse_dynamics)
            return self

        # If dynamics is STDP, test if same as
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            if not self.is_same_as(synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")

            if self.__neuromodulation is not None:
                synapse_dynamics.merge_neuromodulation(self.__neuromodulation)

            # If STDP part matches, return the other, as it might also be
            # structural
            return synapse_dynamics

        # If dynamics is structural but not STDP (as here), merge
        # NOTE: Import here as otherwise we get a circular dependency
        from .synapse_dynamics_structural_stdp import (
            SynapseDynamicsStructuralSTDP)
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            return SynapseDynamicsStructuralSTDP(
                synapse_dynamics.partner_selection, synapse_dynamics.formation,
                synapse_dynamics.elimination,
                self.timing_dependence, self.weight_dependence,
                # voltage dependence is not supported
                None, self.dendritic_delay_fraction,
                synapse_dynamics.f_rew, synapse_dynamics.initial_weight,
                synapse_dynamics.initial_delay, synapse_dynamics.s_max,
                synapse_dynamics.seed,
                backprop_delay=self.backprop_delay)

        # Otherwise, it is static or neuromodulation, so return ourselves
        return self

    @overrides(AbstractPlasticSynapseDynamics.get_value)
    def get_value(self, key):
        for obj in [self.__timing_dependence, self.__weight_dependence, self]:
            if hasattr(obj, key):
                return getattr(obj, key)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @overrides(AbstractPlasticSynapseDynamics.set_value)
    def set_value(self, key, value):
        for obj in [self.__timing_dependence, self.__weight_dependence, self]:
            if hasattr(obj, key):
                setattr(obj, key, value)
                SpynnakerDataView.set_requires_mapping()
                return
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @property
    def weight_dependence(self):
        """
        :rtype: AbstractTimingDependence
        """
        return self.__weight_dependence

    @property
    def timing_dependence(self):
        """
        :rtype: AbstractTimingDependence
        """
        return self.__timing_dependence

    @property
    def dendritic_delay_fraction(self):
        """
        Settable.

        :rtype: float
        """
        return self.__dendritic_delay_fraction

    @dendritic_delay_fraction.setter
    def dendritic_delay_fraction(self, new_value):
        self.__dendritic_delay_fraction = new_value

    @property
    def backprop_delay(self):
        """
        Settable.

        :rtype: bool
        """
        return self.__backprop_delay

    @backprop_delay.setter
    def backprop_delay(self, backprop_delay):
        self.__backprop_delay = bool(backprop_delay)

    @property
    def neuromodulation(self):
        """
        :rtype: SynapseDynamicsNeuromodulation
        """
        return self.__neuromodulation

    @overrides(AbstractPlasticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            return False
        return (
            self.__timing_dependence.is_same_as(
                synapse_dynamics.timing_dependence) and
            self.__weight_dependence.is_same_as(
                synapse_dynamics.weight_dependence) and
            (self.__dendritic_delay_fraction ==
             synapse_dynamics.dendritic_delay_fraction))

    def get_vertex_executable_suffix(self):
        """
        :rtype: str
        """
        # Get the suffix values for timing and weight dependence
        timing_suffix = self.__timing_dependence.vertex_executable_suffix
        weight_suffix = self.__weight_dependence.vertex_executable_suffix

        if self.__neuromodulation:
            name = (
                "_stdp_" +
                self.__neuromodulation.get_vertex_executable_suffix())
        else:
            name = "_stdp_mad_"
        name += timing_suffix + "_" + weight_suffix
        return name

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        """
        :param int n_neurons:
        :param int n_synapse_types:
        :rtype: int
        """
        # 32-bits for back-prop delay
        size = BYTES_PER_WORD
        size += self.__timing_dependence.get_parameters_sdram_usage_in_bytes()
        size += self.__weight_dependence.get_parameters_sdram_usage_in_bytes(
            n_synapse_types, self.__timing_dependence.n_weight_terms)
        if self.__neuromodulation:
            size += self.__neuromodulation.get_parameters_sdram_usage_in_bytes(
                n_neurons, n_synapse_types)
        return size

    @overrides(AbstractPlasticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec, region, global_weight_scale, synapse_weight_scales):
        spec.comment("Writing Plastic Parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)

        # Whether to use back-prop delay
        spec.write_value(int(self.__backprop_delay))

        # Write timing dependence parameters to region
        self.__timing_dependence.write_parameters(
            spec, global_weight_scale, synapse_weight_scales)

        # Write weight dependence information to region
        self.__weight_dependence.write_parameters(
            spec, global_weight_scale, synapse_weight_scales,
            self.__timing_dependence.n_weight_terms)

        if self.__neuromodulation:
            self.__neuromodulation.write_parameters(
                spec, region, global_weight_scale, synapse_weight_scales)

    @property
    def _n_header_bytes(self):
        """
        :rtype: int
        """
        # The header contains a single timestamp and pre-trace
        n_bytes = (
            TIME_STAMP_BYTES + self.__timing_dependence.pre_trace_n_bytes)

        # The actual number of bytes is in a word-aligned struct, so work out
        # the number of bytes as a number of words
        return int(math.ceil(float(n_bytes) / BYTES_PER_WORD)) * BYTES_PER_WORD

    def __get_n_connections(self, n_connections, check_length_padded=True):
        """
        :param int n_connections:
        :param bool check_length_padded:
        :rtype: int
        """
        synapse_structure = self.__timing_dependence.synaptic_structure
        if self.__pad_to_length is not None and check_length_padded:
            n_connections = max(n_connections, self.__pad_to_length)
        if n_connections == 0:
            return 0
        # 2 == two half words per word
        fp_size_words = (
            n_connections // 2 if n_connections % 2 == 0
            else (n_connections + 1) // 2)
        pp_size_bytes = (
            self._n_header_bytes +
            (synapse_structure.get_n_half_words_per_connection() *
             BYTES_PER_SHORT * n_connections))
        # Neuromodulated synapses have the actual weight separately
        if self.__neuromodulation:
            pp_size_bytes += BYTES_PER_SHORT * n_connections
        pp_size_words = int(math.ceil(float(pp_size_bytes) / BYTES_PER_WORD))

        return fp_size_words + pp_size_words

    def get_n_words_for_plastic_connections(self, n_connections):
        """
        :param int n_connections:
        :rtype: int
        """
        return self.__get_n_connections(n_connections)

    @overrides(AbstractPlasticSynapseDynamics.get_plastic_synaptic_data)
    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types, max_n_synapses,
            max_atoms_per_core):
        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        # Get the fixed data
        fixed_plastic = (
            (connections["delay"].astype("uint16") <<
             (n_neuron_id_bits + n_synapse_type_bits)) |
            (connections["synapse_type"].astype("uint16")
             << n_neuron_id_bits) |
            ((connections["target"].astype("uint16") -
              post_vertex_slice.lo_atom) & neuron_id_mask))
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype="uint8").reshape((-1, 2)),
            max_n_synapses)
        fp_size = self.get_n_items(fixed_plastic_rows, BYTES_PER_SHORT)
        if self.__pad_to_length is not None:
            # Pad the data
            fixed_plastic_rows = self._pad_row(
                fixed_plastic_rows, BYTES_PER_SHORT)
        fp_data = self.get_words(fixed_plastic_rows)

        # Get the plastic data by inserting the weight into the half-word
        # specified by the synapse structure
        synapse_structure = self.__timing_dependence.synaptic_structure
        n_half_words = synapse_structure.get_n_half_words_per_connection()
        half_word = synapse_structure.get_weight_half_word()
        # If neuromodulation, the real weight comes first
        if self.__neuromodulation:
            n_half_words += 1
            half_word = 0
        plastic_plastic = numpy.zeros(
            len(connections) * n_half_words, dtype="uint16")
        plastic_plastic[half_word::n_half_words] = \
            numpy.rint(numpy.abs(connections["weight"])).astype("uint16")

        # Convert the plastic data into groups of bytes per connection and
        # then into rows
        plastic_plastic = plastic_plastic.view(dtype="uint8").reshape(
            (-1, n_half_words * BYTES_PER_SHORT))
        plastic_plastic_row_data = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows, plastic_plastic, max_n_synapses)

        # pp_size = fp_size in words => fp_size * no_bytes / 4 (bytes)
        if self.__pad_to_length is not None:
            # Pad the data
            plastic_plastic_row_data = self._pad_row(
                plastic_plastic_row_data, n_half_words * BYTES_PER_SHORT)
        plastic_headers = numpy.zeros(
            (n_rows, self._n_header_bytes), dtype="uint8")
        plastic_plastic_rows = [
            numpy.concatenate((
                plastic_headers[i], plastic_plastic_row_data[i]))
            for i in range(n_rows)]
        pp_size = self.get_n_items(plastic_plastic_rows, BYTES_PER_WORD)
        pp_data = self.get_words(plastic_plastic_rows)

        return fp_data, pp_data, fp_size, pp_size

    def _pad_row(self, rows, no_bytes_per_connection):
        """
        :param list(~numpy.ndarray) rows:
        :param int no_bytes_per_connection:
        :rtype: list(~numpy.ndarray)
        """
        # Row elements are (individual) bytes
        return [
            numpy.concatenate((
                row, numpy.zeros(
                    numpy.clip(
                        (no_bytes_per_connection * self.__pad_to_length -
                         row.size),
                        0, None)).astype(dtype="uint8"))
                ).view(dtype="uint8")
            for row in rows]

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_plastic_plastic_words_per_row)
    def get_n_plastic_plastic_words_per_row(self, pp_size):
        # pp_size is in words, so return
        return pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_fixed_plastic_words_per_row)
    def get_n_fixed_plastic_words_per_row(self, fp_size):
        # fp_size is in half-words
        return numpy.ceil(fp_size / 2.0).astype(dtype="uint32")

    @overrides(AbstractPlasticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, pp_size, fp_size):
        # Each fixed-plastic synapse is a half-word and fp_size is in half
        # words so just return it
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.read_plastic_synaptic_data)
    def read_plastic_synaptic_data(
            self, post_vertex_slice, n_synapse_types, pp_size, pp_data,
            fp_size, fp_data, max_atoms_per_core):
        n_rows = len(fp_size)

        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        data_fixed = numpy.concatenate([
            fp_data[i].view(dtype="uint16")[0:fp_size[i]]
            for i in range(n_rows)])
        pp_without_headers = [
            row.view(dtype="uint8")[self._n_header_bytes:] for row in pp_data]
        synapse_structure = self.__timing_dependence.synaptic_structure
        n_half_words = synapse_structure.get_n_half_words_per_connection()
        half_word = synapse_structure.get_weight_half_word()
        if self.__neuromodulation:
            n_half_words += 1
            half_word = 0
        pp_half_words = numpy.concatenate([
            pp[:size * n_half_words * BYTES_PER_SHORT].view("uint16")[
                half_word::n_half_words]
            for pp, size in zip(pp_without_headers, fp_size)])

        connections = numpy.zeros(
            data_fixed.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = (
            (data_fixed & neuron_id_mask) + post_vertex_slice.lo_atom)
        connections["weight"] = pp_half_words
        connections["delay"] = data_fixed >> (
            n_neuron_id_bits + n_synapse_type_bits)
        return connections

    @overrides(AbstractPlasticSynapseDynamics.get_weight_mean)
    def get_weight_mean(self, connector, synapse_info):
        # Because the weights could all be changed to the maximum, the mean
        # has to be given as the maximum for scaling
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(AbstractPlasticSynapseDynamics.get_weight_variance)
    def get_weight_variance(self, connector, weights, synapse_info):
        # Because the weights could all be changed to the maximum, the variance
        # has to be given as no variance
        return 0.0

    @overrides(AbstractPlasticSynapseDynamics.get_weight_maximum)
    def get_weight_maximum(self, connector, synapse_info):
        w_max = super().get_weight_maximum(connector, synapse_info)
        # The maximum weight is the largest that it could be set to from
        # the weight dependence
        return max(w_max, self.__weight_dependence.weight_maximum)

    @overrides(AbstractPlasticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self):
        names = ['weight', 'delay']
        names.extend(self.__timing_dependence.get_parameter_names())
        names.extend(self.__weight_dependence.get_parameter_names())
        return names

    @overrides(AbstractPlasticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words):
        # Subtract the header size that will always exist
        n_header_words = self._n_header_bytes // BYTES_PER_WORD
        n_words_space = n_words - n_header_words

        # Get plastic plastic size per connection
        synapse_structure = self.__timing_dependence.synaptic_structure
        bytes_per_pp = (
            synapse_structure.get_n_half_words_per_connection() *
            BYTES_PER_SHORT)
        if self.__neuromodulation:
            bytes_per_pp += BYTES_PER_SHORT

        # The fixed plastic size per connection is 2 bytes
        bytes_per_fp = BYTES_PER_SHORT

        # Maximum possible connections, ignoring word alignment
        n_connections = (n_words_space * BYTES_PER_WORD) // (
            bytes_per_pp + bytes_per_fp)

        check_length_padded = False

        # Reduce until correct
        while (self.__get_n_connections(n_connections, check_length_padded) >
               n_words):
            n_connections -= 1

        return n_connections

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self):
        return MatrixGeneratorID.STDP_MATRIX.value

    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(
            self, synaptic_matrix_offset, delayed_matrix_offset, app_edge,
            synapse_info, max_row_info, max_pre_atoms_per_core,
            max_post_atoms_per_core):
        vertex = app_edge.post_vertex
        n_synapse_type_bits = get_n_bits(
            vertex.neuron_impl.get_n_synapse_types())
        n_synapse_index_bits = get_n_bits(max_post_atoms_per_core)
        max_delay = app_edge.post_vertex.splitter.max_support_delay()
        max_delay_bits = get_n_bits(max_delay)
        synapse_struct = self.__timing_dependence.synaptic_structure
        n_half_words = synapse_struct.get_n_half_words_per_connection()
        half_word = synapse_struct.get_weight_half_word()
        if self.__neuromodulation:
            n_half_words += 1
            half_word = 0
        return numpy.array([
            synaptic_matrix_offset, delayed_matrix_offset,
            max_row_info.undelayed_max_n_synapses,
            max_row_info.delayed_max_n_synapses,
            max_row_info.undelayed_max_words, max_row_info.delayed_max_words,
            synapse_info.synapse_type, n_synapse_type_bits,
            n_synapse_index_bits, app_edge.n_delay_stages + 1,
            max_delay, max_delay_bits, app_edge.pre_vertex.n_atoms,
            max_pre_atoms_per_core, self._n_header_bytes // BYTES_PER_SHORT,
            n_half_words, half_word],
            dtype=numpy.uint32)

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self):
        return 17 * BYTES_PER_WORD

    @property
    @overrides(AbstractPlasticSynapseDynamics.changes_during_run)
    def changes_during_run(self):
        return True

    @property
    @overrides(AbstractPlasticSynapseDynamics.weight)
    def weight(self):
        return self.__weight

    @property
    @overrides(AbstractPlasticSynapseDynamics.delay)
    def delay(self):
        return self.__delay

    @property
    @overrides(AbstractPlasticSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self):
        return self.__neuromodulation is None

    @property
    @overrides(AbstractPlasticSynapseDynamics.pad_to_length)
    def pad_to_length(self):
        return self.__pad_to_length
