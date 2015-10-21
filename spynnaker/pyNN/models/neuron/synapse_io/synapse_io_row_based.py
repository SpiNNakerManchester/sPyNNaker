import numpy

from spynnaker.pyNN.models.neuron.synapse_io.abstract_synapse_io \
    import AbstractSynapseIO

_N_HEADER_WORDS = 3


class SynapseIORowBased(AbstractSynapseIO):
    """ A SynapseRowIO implementation that uses a row for each source neuron,
        where each row consists of a fixed region, a plastic region, and a\
        fixed-plastic region (this is the bits of the plastic row that don't\
        actually change).  The plastic region structure is determined by the\
        synapse dynamics of the connector.
    """

    def __init__(self, machine_time_step):
        AbstractSynapseIO.__init__(self)
        self._machine_time_step = machine_time_step

    def get_maximum_delay_supported_in_ms(self):

        # There are 16 slots, one per time step
        return 16 * (self._machine_time_step / 1000.0)

    def get_sdram_usage_in_bytes(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages):

        # Find the maximum row length - i.e. the maximum number of bytes
        # that will be needed by any row for both rows with delay extensions
        # and rows without
        undelayed_max_bytes = 0
        delayed_max_bytes = 0
        max_delay_supported = self.get_maximum_delay_supported_in_ms()
        max_delay = max_delay_supported * (n_delay_stages + 1)

        for synapse_info in synapse_information:
            max_undelayed_row_length = synapse_info.connector\
                .get_n_connections_from_pre_vertex_maximum(
                    n_pre_slices, pre_slice_index, n_post_slices,
                    post_slice_index, pre_vertex_slice, post_vertex_slice,
                    0, max_delay_supported)
            max_delayed_row_length = synapse_info.connector\
                .get_n_connections_from_pre_vertex_maximum(
                    n_pre_slices, pre_slice_index, n_post_slices,
                    post_slice_index, pre_vertex_slice, post_vertex_slice,
                    max_delay_supported + 1, max_delay)

            bytes_per_item = synapse_info.synapse_dynamics\
                .get_n_bytes_per_connection()

            undelayed_max_bytes += bytes_per_item * max_undelayed_row_length
            delayed_max_bytes += bytes_per_item * max_delayed_row_length

        # Add on the header words and multiply by the number of rows in the
        # block
        n_bytes_undelayed = 0
        if undelayed_max_bytes > 0:
            n_bytes_undelayed = _N_HEADER_WORDS + (
                undelayed_max_bytes * pre_vertex_slice.n_atoms)
        n_bytes_delayed = 0
        if delayed_max_bytes > 0:
            n_bytes_delayed = _N_HEADER_WORDS + (
                delayed_max_bytes * pre_vertex_slice.n_atoms * n_delay_stages)
        return (n_bytes_undelayed, n_bytes_delayed)

    @staticmethod
    def _convert_data(fixed_fixed_data_items, fixed_plastic_data_items,
                      plastic_plastic_data_items):
        all_data = list()
        all_data_lengths = list()
        for data in [fixed_fixed_data_items, fixed_plastic_data_items,
                     plastic_plastic_data_items]:
            merged_data = [numpy.pad(
                numpy.concatenate(items), (0, (4 - items.size % 4) & 0x3),
                mode="constant", constant_values=0).view("uint32")
                for items in zip(*data)]
            all_data.append(merged_data)
            all_data_lengths.append(numpy.array(
                [items.size for items in merged_data]))
        return all_data, all_data_lengths

    def get_synapses(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales):

        # Gather the connectivity data
        max_delay = self.get_maximum_delay_supported_in_ms()
        fixed_fixed_data_items = list()
        fixed_plastic_data_items = list()
        plastic_plastic_data_items = list()
        delayed_fixed_fixed_data_items = list()
        delayed_fixed_plastic_data_items = list()
        delayed_plastic_plastic_data_items = list()
        for synapse_info in synapse_information:

            # Get the actual connections
            connections = synapse_info.connector.create_synaptic_block(
                n_pre_slices, pre_slice_index, n_post_slices,
                post_slice_index, pre_vertex_slice, post_vertex_slice,
                synapse_info.synapse_type)

            # Split the connections up based on the delays
            undelayed_connections = connections
            delayed_connections = []
            if max_delay is not None:
                delay_mask = (connections["delay"] <= max_delay)
                undelayed_connections = connections[numpy.where(delay_mask)]
                delayed_connections = connections[numpy.where(~delay_mask)]

            # Get which row each connection will go into
            undelayed_row_indices = []
            if len(undelayed_connections) > 0:
                undelayed_row_indices = numpy.digitize(
                    undelayed_connections["source"], numpy.arange(
                        pre_vertex_slice.lo_atom,
                        pre_vertex_slice.hi_atom + 1),
                    right=True)

            delayed_row_indices = []
            if len(delayed_connections) > 0:

                # Convert the delayed source indices into source index *
                # delay stage
                delayed_row_indices = numpy.digitize(
                    delayed_connections["source"], numpy.arange(
                        pre_vertex_slice.lo_atom,
                        pre_vertex_slice.hi_atom + 1),
                    right=True) * numpy.floor(
                        (numpy.round(delayed_connections["delay"] - 1.0)) /
                        max_delay) - 1

            # Get the data for the connections
            if len(undelayed_connections) > 0:
                fixed_fixed_data, fixed_plastic_data, plastic_plastic_data =\
                    synapse_info.synapse_dynamics.get_synaptic_data(
                        undelayed_connections, self._machine_time_step,
                        n_synapse_types, weight_scales)
                fixed_fixed_data_items.append(numpy.ravel(
                    [fixed_fixed_data[undelayed_row_indices == i]
                     for i in pre_vertex_slice]))
                fixed_plastic_data_items.append(numpy.ravel(
                    [fixed_plastic_data[undelayed_row_indices == i]
                     for i in pre_vertex_slice]))
                plastic_plastic_data_items.append(numpy.ravel(
                    [plastic_plastic_data[undelayed_row_indices == i]
                     for i in pre_vertex_slice]))

            # Get the data for the delayed connections
            if len(delayed_connections) > 0:
                fixed_fixed_data, fixed_plastic_data, plastic_plastic_data =\
                    synapse_info.synapse_dynamics.get_synaptic_data(
                        delayed_connections, self._machine_time_step,
                        n_synapse_types, weight_scales)
                delayed_fixed_fixed_data_items.append(numpy.ravel(
                    [fixed_fixed_data[delayed_row_indices == i]
                     for i in range(pre_slice_index)]))
                delayed_fixed_plastic_data_items.append(numpy.ravel(
                    [fixed_plastic_data[delayed_row_indices == i]
                     for i in range(pre_slice_index)]))
                delayed_plastic_plastic_data_items.append(numpy.ravel(
                    [plastic_plastic_data[delayed_row_indices == i]
                     for i in range(pre_slice_index)]))

        # Join up the individual connectivity data and get the lengths
        (fixed_fixed, fixed_plastic, plastic_plastic,
         ff_size, fp_size, pp_size) = self._convert_data(
            fixed_fixed_data_items, fixed_plastic_data_items,
            plastic_plastic_data_items)
        del fixed_fixed_data_items, fixed_plastic_data_items
        del plastic_plastic_data_items

        # Create the rows with the headers
        items_to_join = [pp_size, plastic_plastic, ff_size, fp_size,
                         fixed_fixed, fixed_plastic]
        rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
        del fixed_fixed, fixed_plastic, plastic_plastic

        # Pad the rows to make them all the same length as the biggest
        row_lengths = [row.size for row in rows]
        max_length = max(row_lengths)
        row_data = []
        if max_length > 0:
            max_length = population_table.get_allowed_row_length(max_length)
            row_data = numpy.concatenate([numpy.pad(
                row, (0, max_length - row.size), mode="constant",
                constant_values=0xBBCCDDEE) for row in rows])

        # Do the same for delayed rows
        (delayed_fixed_fixed, delayed_fixed_plastic, delayed_plastic_plastic,
         delayed_ff_size, delayed_fp_size,
         delayed_pp_size) = self._convert_data(
            delayed_fixed_fixed_data_items, delayed_fixed_plastic_data_items,
            delayed_plastic_plastic_data_items)
        del delayed_fixed_fixed_data_items, delayed_fixed_plastic_data_items
        del delayed_plastic_plastic_data_items

        # Create the rows with the headers
        items_to_join = [delayed_pp_size, delayed_plastic_plastic,
                         delayed_ff_size, delayed_fp_size,
                         delayed_fixed_fixed, delayed_fixed_plastic]
        delayed_rows = [numpy.concatenate(items)
                        for items in zip(*items_to_join)]
        del delayed_fixed_fixed, delayed_fixed_plastic, delayed_plastic_plastic

        # Pad the rows to make them all the same length as the biggest
        row_lengths = [row.size for row in delayed_rows]
        max_length = max(row_lengths)
        delayed_row_data = []
        if max_length > 0:
            max_length = population_table.get_allowed_row_length(max_length)
            delayed_row_data = numpy.concatenate([numpy.pad(
                row, (0, max_length - row.size), mode="constant",
                constant_values=0xBBCCDDEE) for row in delayed_rows])

        return row_data, delayed_row_data
