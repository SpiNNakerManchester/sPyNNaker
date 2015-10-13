from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseDynamics(object):

    @abstractmethod
    def get_synapse_structure(self):
        """ Get the synapse structure for this set of synapse dynamics
        """

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
    def get_synapses_sdram_usage_in_bytes(
            self, connectors, pre_vertex_slice, post_vertex_slice):
        """ Get the SDRAM usage of the synapses for the given pre and post\
            vertex slices
        """

    @abstractmethod
    def get_delayed_synapses_sdram_usage_in_bytes(
            self, connector, pre_vertex_slice, post_vertex_slice,
            min_delay, max_delay):
        """ Get the SDRAM usage of the synapses for a range of delays and for\
            the given pre and post vertex slices
        """

    @abstractmethod
    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        """ Write the synapse parameters to the spec
        """

    @abstractmethod
    def write_synapse_data(
            self, spec, region, synapse_data_list, n_synapse_type_bits,
            population_table_type, next_block_start_address):
        """ Write the synapse data to the spec
        """

    @abstractmethod
    def read_synapse_data(self, region, key):
        """ Read the synapse data for the given key from the given region
        """

    @abstractmethod
    def is_same(self, synapse_dynamics):
        """ Determines if this synapse dynamics is the same as another
        """

    def get_delay_maximum(self, connection):
        """ Get the maximum delay for the synapses
        """
        return connection.get_delay_maximum()

    def get_n_connections_from_pre_vertex_maximum(
            self, connection, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice (or all in the pre vertex if\
            pre_vertex_slice is None) to neurons in the post_vertex_slice
        """
        return connection.get_n_connections_from_pre_vertex_maximum(
            pre_vertex_slice, post_vertex_slice)

    def get_n_connections_from_pre_vertex_with_delay_maximum(
            self, connection, pre_vertex_slice, post_vertex_slice,
            min_delay, max_delay):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice (or all in the pre vertex if\
            pre_vertex_slice is None) to neurons in the post_vertex_slice,\
            for connections with a delay between min_delay and max_delay\
            (inclusive)
        """
        return connection.get_n_connections_from_pre_vertex_with_delay_maximum(
            pre_vertex_slice, post_vertex_slice, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, connection, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those to each of the\
            neurons in the post_vertex_slice from neurons in the\
            pre_vertex_slice
        """
        return connection.get_n_connections_to_post_vertex_maximum(
            pre_vertex_slice, post_vertex_slice)

    def get_weight_mean(self, connection):
        """ Get the mean weight for the synapses
        """
        return connection.get_weight_mean()

    def get_weight_maximum(self, connection):
        """ Get the maximum weight for the synapses
        """
        return connection.get_weight_maximum()

    def get_weight_variance(self, connection):
        """ Get the variance in weight for the synapses
        """
        return connection.get_weight_variance()
