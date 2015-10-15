import math
import numpy

from spynnaker.pyNN.models.neuron.synapse_writers.abstract_synapse_io \
    import AbstractSynapseIO

_N_HEADER_WORDS = 3


class SynapseIORowBased(AbstractSynapseIO):
    """ A SynapseRowIO implementation that uses a row for each source neuron,
        where each row consists of a fixed region, a plastic region, and a\
        fixed-plastic region (this is the bits of the plastic row that don't\
        actually change).  The plastic region structure is determined by the\
        synapse dynamics of the connector.
    """

    def __init__(self):
        AbstractSynapseIO.__init__(self)

    def get_sdram_usage_in_bytes(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, ms_per_delay_stage, min_delay, max_delay):

        # Find the maximum row length - i.e. the maximum number of bytes
        # that will be needed by any row
        max_bytes = 0
        for synapse_info in synapse_information:

            max_bytes = max(
                synapse_info.synapse_dynamics.get_max_bytes_per_source_neuron(
                    synapse_info.connector, n_pre_slices, pre_slice_index,
                    n_post_slices, post_slice_index, pre_vertex_slice,
                    post_vertex_slice, ms_per_delay_stage,
                    min_delay, max_delay),
                max_bytes)

        # Work out how many rows there will be, given the delay stages
        n_delay_stages = int(math.ceil(float(max_delay - min_delay) /
                                       float(ms_per_delay_stage)))
        if n_delay_stages == 0:
            n_delay_stages = 1
        n_rows = pre_vertex_slice.n_atoms * n_delay_stages

        # Add on the header words and multiply by the number of rows in the
        # block
        return _N_HEADER_WORDS + (max_bytes * n_rows)

    def write_synapses(
            self, spec, region, synapse_information, n_pre_slices,
            pre_slice_index, n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, ms_per_delay_stage, min_delay, max_delay,
            population_table, delay_scale, weight_scales):

        # Gather the connectivity data
        fixed_fixed_data_items = list()
        fixed_plastic_data_items = list()
        plastic_plastic_data_items = list()
        for synapse_info in synapse_information:
            synapse_dynamics = synapse_info.synapse_dynamics
            fixed_fixed_data, fixed_plastic_data, plastic_plastic_data =\
                synapse_dynamics.get_synaptic_data_as_row_per_source_neuron(
                    synapse_info.connector, n_pre_slices, pre_slice_index,
                    n_post_slices, post_slice_index, pre_vertex_slice,
                    post_vertex_slice, ms_per_delay_stage, min_delay,
                    max_delay, delay_scale, weight_scales)
            fixed_fixed_data_items.append(fixed_fixed_data)
            fixed_plastic_data_items.append(fixed_plastic_data)
            plastic_plastic_data_items.append(plastic_plastic_data)

        # Join up the individual connectivity data and get the lengths
        all_data = list()
        all_data_lengths = list()
        for data in [fixed_fixed_data_items, fixed_plastic_data_items,
                     plastic_plastic_data_items]:
            merged_data = [numpy.concatenate(items) for items in zip(*data)]
            all_data.append(merged_data)
            all_data_lengths.append(numpy.array(
                [items.size for items in merged_data]))
        fixed_fixed, fixed_plastic, plastic_plastic = all_data
        ff_size, fp_size, pp_size = all_data_lengths
        del data, all_data, all_data_lengths, merged_data
        del fixed_fixed_data_items, fixed_plastic_data_items
        del plastic_plastic_data_items

        # Create the rows with the headers
        items_to_join = [pp_size, plastic_plastic, ff_size, fp_size,
                         fixed_fixed, fixed_plastic]
        rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
        del fixed_fixed, fixed_plastic, plastic_plastic

        # Pad the rows to make them all the same length as the biggest
        row_lengths = [row.size for row in rows]
        max_length = population_table.get_allowed_row_length(max(row_lengths))
        rows = numpy.concatenate([numpy.pad(
            row, (0, max_length - row.size), mode="constant",
            constant_values=0xBBCCDDEE) for row in rows])

        spec.switch_write_focus(region)
        spec.write_array(rows)
