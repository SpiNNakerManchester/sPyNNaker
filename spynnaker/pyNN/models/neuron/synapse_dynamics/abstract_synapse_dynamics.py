from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseDynamics(object):

    @abstractmethod
    def are_weights_signed(self):
        """ Determines if the weights are signed values
        """

    @abstractmethod
    def get_vertex_executable_suffix(self):
        """ Get the executable suffix for a vertex for this dynamics
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        """ Get the SDRAM usage of the synapse dynamics parameters in bytes
        """

    @abstractmethod
    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        """ Write the synapse parameters to the spec
        """

    @abstractmethod
    def get_n_bytes_per_connection(self):
        """ Get the number of bytes per connection
        """

    @abstractmethod
    def get_max_bytes_per_source_neuron(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay, max_delay):
        """ Get the maximum number of bytes needed to represent the\
            connectivity out of the connections from the source neurons in\
            pre_vertex_slice to those in post_vertex_slice
        """

    @abstractmethod
    def get_synaptic_data_as_row_per_source_neuron(
            self, connector, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, ms_per_delay_stage, min_delay,
            max_delay, delay_scale, weight_scales):
        """ Get the fixed-fixed, fixed-plastic and plastic-plastic data for\
            the given connector, pre_vertex_slice and post_vertex_slice.  Data\
            is returned as an array containing an array of uint32 data for\
            each source neuron
        """

    @abstractmethod
    def is_same_as(self, synapse_dynamics):
        """ Determines if this synapse dynamics is the same as another
        """

    def get_delay_maximum(self, connector):
        """ Get the maximum delay for the synapses
        """
        return connector.get_delay_maximum()

    def get_n_connections_from_pre_vertex_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice (or all in the pre vertex if\
            pre_vertex_slice is None) to neurons in the post_vertex_slice
        """
        return connector.get_n_connections_from_pre_vertex_maximum(
            pre_vertex_slice, post_vertex_slice)

    def get_n_connections_from_pre_vertex_with_delay_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice,
            min_delay, max_delay):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice (or all in the pre vertex if\
            pre_vertex_slice is None) to neurons in the post_vertex_slice,\
            for connections with a delay between min_delay and max_delay\
            (inclusive)
        """
        return connector.get_n_connections_from_pre_vertex_with_delay_maximum(
            pre_vertex_slice, post_vertex_slice, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those to each of the\
            neurons in the post_vertex_slice from neurons in the\
            pre_vertex_slice
        """
        return connector.get_n_connections_to_post_vertex_maximum(
            pre_vertex_slice, post_vertex_slice)

    def get_weight_mean(self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the mean weight for the synapses
        """
        return connector.get_weight_mean()

    def get_weight_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum weight for the synapses
        """
        return connector.get_weight_maximum()

    def get_weight_variance(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the variance in weight for the synapses
        """
        return connector.get_weight_variance()
