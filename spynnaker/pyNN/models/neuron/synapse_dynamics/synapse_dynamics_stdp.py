import math
import numpy
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spynnaker.pyNN.models.abstract_models import AbstractSettable
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.utility_calls import get_n_bits

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4
# When not using the MAD scheme, how many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4


class SynapseDynamicsSTDP(
        AbstractPlasticSynapseDynamics, AbstractSettable,
        AbstractChangableAfterRun, AbstractGenerateOnMachine):
    __slots__ = [
        # Flag: whether there is state in this class that is not reflected on
        # the SpiNNaker system
        "__change_requires_mapping",
        # Fraction of delay that is dendritic (instead of axonal or synaptic)
        "__dendritic_delay_fraction",
        # timing dependence to use for the STDP rule
        "__timing_dependence",
        # weight dependence to use for the STDP rule
        "__weight_dependence",
        # padding to add to a synaptic row for synaptic rewiring
        "__pad_to_length"]

    def __init__(
            self, timing_dependence=None, weight_dependence=None,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            pad_to_length=None):
        self.__timing_dependence = timing_dependence
        self.__weight_dependence = weight_dependence
        self.__dendritic_delay_fraction = float(dendritic_delay_fraction)
        self.__change_requires_mapping = True
        self.__pad_to_length = pad_to_length

        if not (0.5 <= self.__dendritic_delay_fraction <= 1.0):
            raise NotImplementedError(
                "dendritic_delay_fraction must be in the interval [0.5, 1.0]")

        if timing_dependence is None or weight_dependence is None:
            raise NotImplementedError(
                "Both timing_dependence and weight_dependence must be"
                "specified")

        if voltage_dependence is not None:
            raise NotImplementedError(
                "Voltage dependence has not been implemented")

    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        """ True if changes that have been made require that mapping be\
            performed.  Note that this should return True the first time it\
            is called, as the vertex must require mapping as it has been\
            created!
        """
        return self.__change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        """ Marks the point after which changes are reported.  Immediately\
            after calling this method, requires_mapping should return False.
        """
        self.__change_requires_mapping = False

    @overrides(AbstractSettable.get_value)
    def get_value(self, key):
        """ Get a property
        """
        for obj in [self.__timing_dependence, self.__weight_dependence, self]:
            if hasattr(obj, key):
                return getattr(obj, key)
        raise InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @overrides(AbstractSettable.set_value)
    def set_value(self, key, value):
        """ Set a property

        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """
        for obj in [self.__timing_dependence, self.__weight_dependence, self]:
            if hasattr(obj, key):
                setattr(obj, key, value)
                self.__change_requires_mapping = True
                return
        raise InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @property
    def weight_dependence(self):
        return self.__weight_dependence

    @property
    def timing_dependence(self):
        return self.__timing_dependence

    @property
    def dendritic_delay_fraction(self):
        return self.__dendritic_delay_fraction

    @dendritic_delay_fraction.setter
    def dendritic_delay_fraction(self, new_value):
        self.__dendritic_delay_fraction = new_value

    def is_same_as(self, synapse_dynamics):
        # pylint: disable=protected-access
        if not isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            return False
        return (
            self.__timing_dependence.is_same_as(
                synapse_dynamics.timing_dependence) and
            self.__weight_dependence.is_same_as(
                synapse_dynamics.weight_dependence) and
            (self.__dendritic_delay_fraction ==
             synapse_dynamics.dendritic_delay_fraction))

    def are_weights_signed(self):
        return False

    def get_vertex_executable_suffix(self):
        name = "_stdp_mad"
        name += "_" + self.__timing_dependence.vertex_executable_suffix
        name += "_" + self.__weight_dependence.vertex_executable_suffix
        return name

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        size = self.__timing_dependence.get_parameters_sdram_usage_in_bytes()
        size += self.__weight_dependence.get_parameters_sdram_usage_in_bytes(
            n_synapse_types, self.__timing_dependence.n_weight_terms)
        return size

    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        spec.comment("Writing Plastic Parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)

        # Write timing dependence parameters to region
        self.__timing_dependence.write_parameters(
            spec, machine_time_step, weight_scales)

        # Write weight dependence information to region
        self.__weight_dependence.write_parameters(
            spec, machine_time_step, weight_scales,
            self.__timing_dependence.n_weight_terms)

    @property
    def _n_header_bytes(self):
        # The header contains a single timestamp and pre-trace
        n_bytes = (
            TIME_STAMP_BYTES + self.__timing_dependence.pre_trace_n_bytes)

        # The actual number of bytes is in a word-aligned struct, so work out
        # the number of bytes as a number of words
        return int(math.ceil(float(n_bytes) / 4.0)) * 4

    def get_n_words_for_plastic_connections(self, n_connections):
        synapse_structure = self.__timing_dependence.synaptic_structure
        if self.__pad_to_length is not None:
            n_connections = max(n_connections, self.__pad_to_length)
        if n_connections == 0:
            return 0
        fp_size_words = (
            n_connections // 2 if n_connections % 2 == 0
            else (n_connections + 1) // 2)
        pp_size_bytes = (
            self._n_header_bytes +
            (synapse_structure.get_n_half_words_per_connection() *
             2 * n_connections))
        pp_size_words = int(math.ceil(float(pp_size_bytes) / 4.0))

        return fp_size_words + pp_size_words

    @overrides(AbstractPlasticSynapseDynamics.get_plastic_synaptic_data)
    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types):
        # pylint: disable=too-many-arguments
        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        dendritic_delays = (
            connections["delay"] * self.__dendritic_delay_fraction)
        axonal_delays = (
            connections["delay"] * (1.0 - self.__dendritic_delay_fraction))

        # Get the fixed data
        fixed_plastic = (
            ((dendritic_delays.astype("uint16") & 0xF) <<
             (n_neuron_id_bits + n_synapse_type_bits)) |
            ((axonal_delays.astype("uint16") & 0xF) <<
             (4 + n_neuron_id_bits + n_synapse_type_bits)) |
            (connections["synapse_type"].astype("uint16")
             << n_neuron_id_bits) |
            ((connections["target"].astype("uint16") -
              post_vertex_slice.lo_atom) & neuron_id_mask))
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype="uint8").reshape((-1, 2)))
        fp_size = self.get_n_items(fixed_plastic_rows, 2)
        if self.__pad_to_length is not None:
            # Pad the data
            fixed_plastic_rows = self._pad_row(fixed_plastic_rows, 2)
        fp_data = self.get_words(fixed_plastic_rows)

        # Get the plastic data by inserting the weight into the half-word
        # specified by the synapse structure
        synapse_structure = self.__timing_dependence.synaptic_structure
        n_half_words = synapse_structure.get_n_half_words_per_connection()
        half_word = synapse_structure.get_weight_half_word()
        plastic_plastic = numpy.zeros(
            len(connections) * n_half_words, dtype="uint16")
        plastic_plastic[half_word::n_half_words] = \
            numpy.rint(connections["weight"]).astype("uint16")

        # Convert the plastic data into groups of bytes per connection and
        # then into rows
        plastic_plastic = plastic_plastic.view(dtype="uint8").reshape(
            (-1, n_half_words * 2))
        plastic_plastic_row_data = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows, plastic_plastic)

        # pp_size = fp_size in words => fp_size * no_bytes / 4 (bytes)
        if self.__pad_to_length is not None:
            # Pad the data
            plastic_plastic_row_data = self._pad_row(
                plastic_plastic_row_data, n_half_words * 2)
        plastic_headers = numpy.zeros(
            (n_rows, self._n_header_bytes), dtype="uint8")
        plastic_plastic_rows = [
            numpy.concatenate((
                plastic_headers[i], plastic_plastic_row_data[i]))
            for i in range(n_rows)]
        pp_size = self.get_n_items(plastic_plastic_rows, 4)
        pp_data = self.get_words(plastic_plastic_rows)

        return fp_data, pp_data, fp_size, pp_size

    def _pad_row(self, rows, no_bytes_per_connection):
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
            fp_size, fp_data):
        # pylint: disable=too-many-arguments
        n_rows = len(fp_size)

        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        data_fixed = numpy.concatenate([
            fp_data[i].view(dtype="uint16")[0:fp_size[i]]
            for i in range(n_rows)])
        pp_without_headers = [
            row.view(dtype="uint8")[self._n_header_bytes:] for row in pp_data]
        synapse_structure = self.__timing_dependence.synaptic_structure
        n_half_words = synapse_structure.get_n_half_words_per_connection()
        half_word = synapse_structure.get_weight_half_word()
        pp_half_words = numpy.concatenate([
            pp[:size * n_half_words * 2].view("int16")[
                half_word::n_half_words]
            for pp, size in zip(pp_without_headers, fp_size)])

        connections = numpy.zeros(
            data_fixed.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = (
            (data_fixed & neuron_id_mask) + post_vertex_slice.lo_atom)
        connections["weight"] = pp_half_words
        connections["delay"] = (data_fixed >> (
            n_neuron_id_bits + n_synapse_type_bits)) & 0xF
        connections["delay"][connections["delay"] == 0] = 16
        return connections

    def get_weight_mean(self, connector, weights):
        # pylint: disable=too-many-arguments

        # Because the weights could all be changed to the maximum, the mean
        # has to be given as the maximum for scaling
        return self.__weight_dependence.weight_maximum

    def get_weight_variance(self, connector, weights):
        # pylint: disable=too-many-arguments

        # Because the weights could all be changed to the maximum, the variance
        # has to be given as no variance
        return 0.0

    def get_weight_maximum(self, connector, weights):
        # pylint: disable=too-many-arguments

        # The maximum weight is the largest that it could be set to from
        # the weight dependence
        return self.__weight_dependence.weight_maximum

    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        if self.__timing_dependence is not None:
            prov_data.extend(self.__timing_dependence.get_provenance_data(
                pre_population_label, post_population_label))
        if self.__weight_dependence is not None:
            prov_data.extend(self.__weight_dependence.get_provenance_data(
                pre_population_label, post_population_label))
        return prov_data

    @overrides(AbstractPlasticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self):
        names = ['weight', 'delay']
        if self.__timing_dependence is not None:
            names.extend(self.__timing_dependence.get_parameter_names())
        if self.__weight_dependence is not None:
            names.extend(self.__weight_dependence.get_parameter_names())
        return names

    @overrides(AbstractPlasticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words):

        # Subtract the header size that will always exist
        n_header_words = self._n_header_bytes // 4
        n_words_space = n_words - n_header_words

        # Get plastic plastic size per connection
        synapse_structure = self.__timing_dependence.synaptic_structure
        bytes_per_pp = synapse_structure.get_n_half_words_per_connection() * 2

        # The fixed plastic size per connection is 2 bytes
        bytes_per_fp = 2

        # Maximum possible connections, ignoring word alignment
        n_connections = (n_words_space * 4) // (bytes_per_pp + bytes_per_fp)

        # Reduce until correct
        while (self.get_n_words_for_plastic_connections(n_connections) >
               n_words):
            n_connections -= 1

        return n_connections

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self):
        return MatrixGeneratorID.STDP_MATRIX.value

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(self):
        synapse_struct = self.__timing_dependence.synaptic_structure
        return numpy.array([
            self._n_header_bytes // 2,
            synapse_struct.get_n_half_words_per_connection(),
            synapse_struct.get_weight_half_word()], dtype="uint32")

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self):
        return 3 * 4
