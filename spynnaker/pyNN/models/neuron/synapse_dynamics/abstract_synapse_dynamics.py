from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseDynamics(object):

    @abstractmethod
    def is_same_as(self, synapse_dynamics):
        """ Determines if this synapse dynamics is the same as another
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
    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        """ Write the synapse parameters to the spec
        """

    @abstractmethod
    def get_n_bytes_per_connection(self):
        """ Get the number of bytes per connection
        """

    @abstractmethod
    def get_synaptic_data(
            self, connections, machine_time_step, n_synapse_types,
            weight_scales, synapse_type):
        """ Get the fixed-fixed, fixed-plastic and plastic-plastic data for\
            the given connections.  Data is returned as an array of arrays of\
            words for each connection
        """

    def get_delay_maximum(self, connector):
        """ Get the maximum delay for the synapses
        """
        return connector.get_delay_maximum()

    def get_weight_mean(self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the mean weight for the synapses
        """
        return connector.get_weight_mean(pre_vertex_slice, post_vertex_slice)

    def get_weight_maximum(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum weight for the synapses
        """
        return connector.get_weight_maximum(
            pre_vertex_slice, post_vertex_slice)

    def get_weight_variance(
            self, connector, pre_vertex_slice, post_vertex_slice):
        """ Get the variance in weight for the synapses
        """
        return connector.get_weight_variance(
            pre_vertex_slice, post_vertex_slice)
