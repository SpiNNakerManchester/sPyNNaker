import math
import numpy

from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# When not using the MAD scheme, how many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4


class SynapseDynamicsSTDP(AbstractSynapseDynamics):

    def __init__(
            self, timing_dependence=None, weight_dependence=None,
            voltage_dependence=None,
            dendritic_delay_fraction=1.0, mad=True):
        AbstractSynapseDynamics.__init__(self)
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
        name = "stdp_mad" if self._mad else "stdp"
        name += "_" + self._timing_dependence.vertex_executable_suffix
        name += "_" + self._weight_dependence.vertex_executable_suffix
        return name

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        size = 0

        size += self._timing_dependence.get_paramters_sdram_usage_in_bytes()
        size += self._weight_dependence.get_paramters_sdram_usage_in_bytes(
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
        if self._mad:

            # If we're using MAD, the header contains a single timestamp and
            # pre-trace
            return (
                TIME_STAMP_BYTES + self.timing_dependence.pre_trace_n_bytes)
        else:

            # Otherwise, headers consist of a counter followed by
            # NUM_PRE_SYNAPTIC_EVENTS timestamps and pre-traces
            return (
                4 + (NUM_PRE_SYNAPTIC_EVENTS *
                     (TIME_STAMP_BYTES +
                      self.timing_dependence.pre_trace_n_bytes)))

    def get_n_bytes_for_connections(self, n_connections):
        synapse_structure = self._timing_dependence.synaptic_structure

        return (
            self._n_header_bytes +
            (2 * n_connections) +
            synapse_structure.get_n_bytes_for_connections(n_connections))

    def get_synaptic_data(
            self, connections, post_vertex_slice, n_synapse_types,
            weight_scales, synapse_type):
        """ Get the fixed-fixed, fixed-plastic and plastic-plastic data for\
            the given connections.  Data is returned as an array of arrays of\
            bytes for each connection
        """
        synapse_weight_scale = weight_scales[synapse_type]
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))
        dendritic_delays = (
            connections["delay"] * self._dendritic_delay_fraction)
        axonal_delays = (
            connections["delay"] * (1.0 - self._dendritic_delay_fraction))

        fixed_plastic = (
            ((dendritic_delays.astype("uint32") & 0xF) <<
             (8 + n_synapse_type_bits)) |
            ((axonal_delays.astype("uint32") & 0xF) <<
             (12 + n_synapse_type_bits)) |
            (synapse_type << 8) |
            ((connections["target"] - post_vertex_slice.lo_atom) & 0xFF))

        synapse_structure = self._timing_dependence.synaptic_structure
        plastic_plastic = synapse_structure.get_synaptic_data(
            connections, synapse_weight_scale)
        plastic_plastic = numpy.concatenate(
            numpy.zeros(self._n_header_bytes, dtype='uint8'),
            plastic_plastic)

        return (None, fixed_plastic.view(dtype="uint8").reshape((-1, 4)),
                plastic_plastic)

    def get_weight_mean(self, connector, pre_vertex_slice, post_vertex_slice):

        # Because the weights could all be changed to the maximum, the mean
        # has to be given as the maximum for scaling
        return self._weight_dependence.maximum_weight

    def get_weight_variance(
            self, connector, pre_vertex_slice, post_vertex_slice):

        # Because the weights could all be changed to the maximum, the variance
        # has to be given as no variance
        return 0.0

    def get_weight_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice):

        # The maximum weight is the largest that it could be set to from
        # the weight dependence
        return self._weight_dependence.maximum_weight
