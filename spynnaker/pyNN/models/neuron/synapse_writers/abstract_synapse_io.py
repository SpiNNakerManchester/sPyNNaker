from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseIO(object):

    @abstractmethod
    def get_sdram_usage_in_bytes(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, ms_per_delay_stage, min_delay, max_delay):
        """ Get the SDRAM usage of a list of synapse information objects for\
            the given slices, and given splitting of delays
        """

    @abstractmethod
    def write_synapses(
            self, spec, region, synapse_information, n_pre_slices,
            pre_slice_index, n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, ms_per_delay_stage, min_delay, max_delay,
            population_table, delay_scale, weight_scales):
        """ Write the synapses to a given region of a data specification
        """
