from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSynapseIO(object):
    # pylint: disable=too-many-arguments

    __slots__ = ()

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by the synapse representation \
            before extensions are required, or None if any delay is supported
        """

    def get_max_row_info(
            self, synapse_info, post_vertex_slice, n_delay_stages,
            population_table, machine_time_step, in_edge):
        """ Get the information about the maximum lengths of delayed and\
            undelayed rows in bytes (including header), words (without header)\
            and number of synapses
        """

    @abstractmethod
    def get_synapses(
            self, synapse_info, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales, machine_time_step,
            app_edge, machine_edge):
        """ Get the synapses as an array of words for non-delayed synapses and\
            an array of words for delayed synapses
        """

    @abstractmethod
    def read_synapses(
            self, synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            weight_scales, data, delayed_data, n_delay_stages,
            machine_time_step):
        """ Read the synapses for a given projection synapse information\
            object out of the given data
        """

    @abstractmethod
    def get_block_n_bytes(self, max_row_length, n_rows):
        """ Get the number of bytes in a block given the max row length and\
            number of rows
        """
