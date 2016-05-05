from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod

import numpy
import math


@add_metaclass(ABCMeta)
class AbstractSynapseDynamics(object):

    NUMPY_CONNECTORS_DTYPE = [("source", "uint32"), ("target", "uint32"),
                              ("weight", "float64"), ("delay", "float64")]

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

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get the provenance data from this synapse dynamics object
        """
        return list()

    def get_delay_maximum(self, connector):
        """ Get the maximum delay for the synapses
        """
        return connector.get_delay_maximum()

    def get_delay_variance(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the variance in delay for the synapses
        """
        return connector.get_delay_variance(
            n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice)

    def get_weight_mean(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the mean weight for the synapses
        """
        return connector.get_weight_mean(
            n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice)

    def get_weight_maximum(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum weight for the synapses
        """
        return connector.get_weight_maximum(
            n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice)

    def get_weight_variance(
            self, connector, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the variance in weight for the synapses
        """
        return connector.get_weight_variance(
            n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice)

    def convert_per_connection_data_to_rows(
            self, connection_row_indices, n_rows, data):
        """ Converts per-connection data generated from connections into\
            row-based data to be returned from get_synaptic_data
        """
        return [
            data[connection_row_indices == i].reshape(-1)
            for i in range(n_rows)
        ]

    def get_n_items(self, rows, item_size):
        """ Get the number of items in each row as 4-byte values, given the\
            item size
        """
        return numpy.array([
            int(math.ceil(float(row.size) / float(item_size)))
            for row in rows], dtype="uint32").reshape((-1, 1))

    def get_words(self, rows):
        """ Convert the row data to words
        """
        words = [numpy.pad(
            row, (0, (4 - (row.size % 4)) & 0x3), mode="constant",
            constant_values=0).view("uint32") for row in rows]
        return words
