from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseIO(object):

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self):
        """ Get the maximum delay supported by the synapse representation \
            before extensions are required, or None if any delay is supported
        """

    @abstractmethod
    def get_sdram_usage_in_bytes(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table):
        """ Get the SDRAM usage of a list of synapse information objects for\
            the given slices, and given number of delay stages (each stage\
            representing a multiple of the maximum delay supported), returning\
            the size for the undelayed synapse information and the size for\
            the delayed information
        """

    @abstractmethod
    def get_synapses(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales):
        """ Get the synapses as an array of words for undelayed synapses and\
            an array of words for delayed synapses
        """
