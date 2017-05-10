import math
import numpy

from spynnaker.pyNN.models.neuron.synapse_dynamics\
    .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# When not using the MAD scheme, how many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4


class SynapseDynamicsSTDP(AbstractPlasticSynapseDynamics):

    def __init__(
            self, timing_dependence=None, weight_dependence=None,
            voltage_dependence=None,
            dendritic_delay_fraction=1.0, mad=True):
        AbstractPlasticSynapseDynamics.__init__(self)
        self._timing_dependence = timing_dependence
        self._weight_dependence = weight_dependence
        self._dendritic_delay_fraction = float(dendritic_delay_fraction)
        self._mad = mad

        if (self._dendritic_delay_fraction < 0.5 or
                self._dendritic_delay_fraction > 1.0):
            raise NotImplementedError(
                "dendritic_delay_fraction must be in the interval [0.5, 1.0]")

        if self._timing_dependence is None or self._weight_dependence is None:
            raise NotImplementedError(
                "Both timing_dependence and weight_dependence must be"
                "specified")

        if voltage_dependence is not None:
            raise NotImplementedError(
                "Voltage dependence has not been implemented")

    @property
    def weight_dependence(self):
        return self._weight_dependence

    @property
    def timing_dependence(self):
        return self._timing_dependence

    @property
    def dendritic_delay_fraction(self):
        return self._dendritic_delay_fraction

    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            return False
        return (
            self._timing_dependence.is_same_as(
                synapse_dynamics._timing_dependence) and
            self._weight_dependence.is_same_as(
                synapse_dynamics._weight_dependence) and
            (self._dendritic_delay_fraction ==
             synapse_dynamics._dendritic_delay_fraction) and
            (self._mad == synapse_dynamics._mad))

    def are_weights_signed(self):
        return False

    def get_vertex_executable_suffix(self):
        name = "_stdp_mad" if self._mad else "_stdp"
        name += "_" + self._timing_dependence.vertex_executable_suffix
        name += "_" + self._weight_dependence.vertex_executable_suffix
        return name

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        size = 0

        size += self._timing_dependence.get_parameters_sdram_usage_in_bytes()
        size += self._weight_dependence.get_parameters_sdram_usage_in_bytes(
            n_synapse_types, self._timing_dependence.n_weight_terms)

        return size

    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        spec.comment("Writing Plastic Parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)

        # Write timing dependence parameters to region
        self._timing_dependence.write_parameters(
            spec, machine_time_step, weight_scales)

        # Write weight dependence information to region
        self._weight_dependence.write_parameters(
            spec, machine_time_step, weight_scales,
            self._timing_dependence.n_weight_terms)

    @property
    def _n_header_bytes(self):

        n_bytes = 0
        if self._mad:

            # If we're using MAD, the header contains a single timestamp and
            # pre-trace
            n_bytes = (
                TIME_STAMP_BYTES + self.timing_dependence.pre_trace_n_bytes)
        else:

            # Otherwise, headers consist of a counter followed by
            # NUM_PRE_SYNAPTIC_EVENTS timestamps and pre-traces
            n_bytes = (
                4 + (NUM_PRE_SYNAPTIC_EVENTS *
                     (TIME_STAMP_BYTES +
                      self.timing_dependence.pre_trace_n_bytes)))

        # The actual number of bytes is in a word-aligned struct, so work out
        # the number of words
        return int(math.ceil(float(n_bytes) / 4.0)) * 4

    def get_n_words_for_plastic_connections(self, n_connections):
        synapse_structure = self._timing_dependence.synaptic_structure
        fp_size_words = \
            n_connections if n_connections % 2 == 0 else n_connections + 1
        pp_size_bytes = (
            self._n_header_bytes +
            (synapse_structure.get_n_bytes_per_connection() * n_connections))
        pp_size_words = int(math.ceil(float(pp_size_bytes) / 4.0))

        return fp_size_words + pp_size_words

    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types):
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))
        dendritic_delays = (
            connections["delay"] * self._dendritic_delay_fraction)
        axonal_delays = (
            connections["delay"] * (1.0 - self._dendritic_delay_fraction))

        # Get the fixed data
        fixed_plastic = (
            ((dendritic_delays.astype("uint16") & 0xF) <<
             (8 + n_synapse_type_bits)) |
            ((axonal_delays.astype("uint16") & 0xF) <<
             (12 + n_synapse_type_bits)) |
            (connections["synapse_type"].astype("uint16") << 8) |
            ((connections["target"].astype("uint16") -
              post_vertex_slice.lo_atom) & 0xFF))
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype="uint8").reshape((-1, 2)))
        fp_size = self.get_n_items(fixed_plastic_rows, 2)
        fp_data = self.get_words(fixed_plastic_rows)

        # Get the plastic data
        synapse_structure = self._timing_dependence.synaptic_structure
        plastic_plastic = synapse_structure.get_synaptic_data(connections)
        plastic_headers = numpy.zeros(
            (n_rows, self._n_header_bytes), dtype="uint8")
        plastic_plastic_row_data = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows, plastic_plastic)
        plastic_plastic_rows = [
            numpy.concatenate((
                plastic_headers[i], plastic_plastic_row_data[i]))
            for i in range(n_rows)]
        pp_size = self.get_n_items(plastic_plastic_rows, 4)
        pp_data = self.get_words(plastic_plastic_rows)

        return (fp_data, pp_data, fp_size, pp_size)

    def get_n_plastic_plastic_words_per_row(self, pp_size):

        # pp_size is in words, so return
        return pp_size

    def get_n_fixed_plastic_words_per_row(self, fp_size):

        # fp_size is in half-words
        return numpy.ceil(fp_size / 2.0).astype(dtype="uint32")

    def get_n_synapses_in_rows(self, pp_size, fp_size):

        # Each fixed-plastic synapse is a half-word and fp_size is in half
        # words so just return it
        return fp_size

    def read_plastic_synaptic_data(
            self, post_vertex_slice, n_synapse_types, pp_size, pp_data,
            fp_size, fp_data):
        n_rows = len(fp_size)
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))
        data_fixed = numpy.concatenate([
            fp_data[i].view(dtype="uint16")[0:fp_size[i]]
            for i in range(n_rows)])
        pp_without_headers = [
            row.view(dtype="uint8")[self._n_header_bytes:] for row in pp_data]
        synapse_structure = self._timing_dependence.synaptic_structure

        connections = numpy.zeros(
            data_fixed.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = (data_fixed & 0xFF) + post_vertex_slice.lo_atom
        connections["weight"] = synapse_structure.read_synaptic_data(
            fp_size, pp_without_headers)
        connections["delay"] = (data_fixed >> (8 + n_synapse_type_bits)) & 0xF
        connections["delay"][connections["delay"] == 0] = 16
        return connections

    def get_weight_mean(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        # Because the weights could all be changed to the maximum, the mean
        # has to be given as the maximum for scaling
        return self._weight_dependence.weight_maximum

    def get_weight_variance(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        # Because the weights could all be changed to the maximum, the variance
        # has to be given as no variance
        return 0.0

    def get_weight_maximum(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        # The maximum weight is the largest that it could be set to from
        # the weight dependence
        return self._weight_dependence.weight_maximum

    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        if self._timing_dependence is not None:
            prov_data.extend(self._timing_dependence.get_provenance_data(
                pre_population_label, post_population_label))
        if self._weight_dependence is not None:
            prov_data.extend(self._weight_dependence.get_provenance_data(
                pre_population_label, post_population_label))
        return prov_data
