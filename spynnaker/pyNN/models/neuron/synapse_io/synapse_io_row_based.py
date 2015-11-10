import numpy
import math

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
            post_vertex_slice, n_delay_stages, population_table):

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

        # Adjust for the allowed row lengths from the population table
        undelayed_max_bytes = population_table.get_allowed_row_length(
            int(math.ceil(undelayed_max_bytes / 4.0))) * 4
        delayed_max_bytes = population_table.get_allowed_row_length(
            int(math.ceil(delayed_max_bytes / 4.0))) * 4

        # Add on the header words and multiply by the number of rows in the
        # block
        n_bytes_undelayed = 0
        if undelayed_max_bytes > 0:
            n_bytes_undelayed = ((
                (_N_HEADER_WORDS * 4) + undelayed_max_bytes) *
                pre_vertex_slice.n_atoms)
        n_bytes_delayed = 0
        if delayed_max_bytes > 0:
            n_bytes_delayed = ((
                (_N_HEADER_WORDS * 4) + delayed_max_bytes) *
                pre_vertex_slice.n_atoms * n_delay_stages)
        return (n_bytes_undelayed, n_bytes_delayed)

    @staticmethod
    def _convert_data(fixed_fixed_data_items, fixed_plastic_data_items,
                      plastic_plastic_data_items, n_rows):
        all_data = list()
        all_data_lengths = list()
        for data in [fixed_fixed_data_items, fixed_plastic_data_items,
                     plastic_plastic_data_items]:
            merged_data = None
            if len(data) > 0:
                merged_data = [numpy.concatenate(items)
                               for items in zip(*data)]
                merged_data = [numpy.pad(
                    items, (0, (4 - items.size % 4) & 0x3), mode="constant",
                    constant_values=0).view("uint32") for items in merged_data]
                all_data.append(merged_data)
                all_data_lengths.append(numpy.array([
                    numpy.array([items.size], dtype="uint32")
                    for items in merged_data]))
            else:
                all_data.append(numpy.array(
                    [numpy.zeros(0, dtype="uint32")] * n_rows))
                all_data_lengths.append(numpy.array(
                    [numpy.zeros(1, dtype="uint32")] * n_rows))

        return all_data, all_data_lengths

    def get_synapses(
            self, synapse_information, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales):

        # Get delays in timesteps
        max_delay = self.get_maximum_delay_supported_in_ms()
        if max_delay is not None:
            max_delay = max_delay * (1000.0 / self._machine_time_step)

        # Gather the connectivity data
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
                post_slice_index, pre_vertex_slice, post_vertex_slice)

            # Convert delays to timesteps
            connections["delay"] = numpy.rint(
                connections["delay"] * (1000.0 / self._machine_time_step))

            # Split the connections up based on the delays
            undelayed_connections = connections
            delayed_connections = []
            if max_delay is not None:
                delay_mask = (connections["delay"] <= max_delay)
                undelayed_connections = connections[numpy.where(delay_mask)]
                delayed_connections = connections[numpy.where(~delay_mask)]
            del connections

            # Get which row each connection will go into
            undelayed_row_indices = (undelayed_connections["source"] -
                                     pre_vertex_slice.lo_atom)

            # Get the delay stages and which row each delayed connection will
            # go into
            stages = numpy.floor(
                (numpy.round(delayed_connections["delay"] - 1.0)) / max_delay)
            n_stages = 0
            if stages.size > 0:
                n_stages = int(numpy.max(stages))
            delayed_row_indices = (
                (delayed_connections["source"] - pre_vertex_slice.lo_atom) +
                ((stages - 1) * pre_vertex_slice.n_atoms))
            delayed_connections["delay"] -= max_delay * stages
            delayed_source_ids = (delayed_connections["source"] -
                                  pre_vertex_slice.lo_atom)

            # Get the data for the connections
            if len(undelayed_connections) > 0:
                fixed_fixed_data, fixed_plastic_data, plastic_plastic_data =\
                    synapse_info.synapse_dynamics.get_synaptic_data(
                        undelayed_connections, post_vertex_slice,
                        n_synapse_types, weight_scales,
                        synapse_info.synapse_type)
                if fixed_fixed_data is not None:
                    fixed_fixed_data_items.append([numpy.ravel(
                        fixed_fixed_data[undelayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms)])
                if fixed_plastic_data is not None:
                    fixed_plastic_data_items.append([numpy.ravel(
                        fixed_plastic_data[undelayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms)])
                if plastic_plastic_data is not None:
                    plastic_plastic_data_items.append([numpy.ravel(
                        plastic_plastic_data[undelayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms)])
                del fixed_fixed_data, fixed_plastic_data, plastic_plastic_data
            del undelayed_connections

            # Get the data for the delayed connections
            if len(delayed_connections) > 0:
                fixed_fixed_data, fixed_plastic_data, plastic_plastic_data =\
                    synapse_info.synapse_dynamics.get_synaptic_data(
                        delayed_connections, post_vertex_slice,
                        n_synapse_types, weight_scales,
                        synapse_info.synapse_type)
                if fixed_fixed_data is not None:
                    delayed_fixed_fixed_data_items.append([numpy.ravel(
                        fixed_fixed_data[delayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms * n_stages)])
                if fixed_plastic_data is not None:
                    delayed_fixed_plastic_data_items.append([numpy.ravel(
                        fixed_plastic_data[delayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms * n_stages)])
                if plastic_plastic_data is not None:
                    delayed_plastic_plastic_data_items.append([numpy.ravel(
                        plastic_plastic_data[delayed_row_indices == i])
                        for i in range(pre_vertex_slice.n_atoms * n_stages)])
                del fixed_fixed_data, fixed_plastic_data, plastic_plastic_data
            del delayed_connections

        # Join up the individual connectivity data and get the lengths
        row_data = []
        max_row_length = 0
        if sum((len(fixed_fixed_data_items), len(fixed_plastic_data_items),
                len(plastic_plastic_data_items))) > 0:
            ((fixed_fixed, fixed_plastic, plastic_plastic),
             (ff_size, fp_size, pp_size)) = self._convert_data(
                fixed_fixed_data_items, fixed_plastic_data_items,
                plastic_plastic_data_items, pre_vertex_slice.n_atoms)
            del fixed_fixed_data_items
            del fixed_plastic_data_items
            del plastic_plastic_data_items

            # Create the rows with the headers
            items_to_join = [pp_size, plastic_plastic, ff_size, fp_size,
                             fixed_fixed, fixed_plastic]
            rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
            del fixed_fixed, fixed_plastic, plastic_plastic

            # Pad the rows to make them all the same length as the biggest
            row_lengths = [row.size for row in rows]
            max_length = max(row_lengths) - _N_HEADER_WORDS
            max_row_length = max_length
            if max_length > 0:
                max_length = population_table.get_allowed_row_length(
                    max_length)
                row_data = numpy.concatenate([numpy.pad(
                    row, (0, max_length - (row.size - _N_HEADER_WORDS)),
                    mode="constant", constant_values=0x11223344)
                    for row in rows])

        # Do the same for delayed rows
        delayed_row_data = []
        max_delayed_row_length = 0
        if sum((len(delayed_fixed_fixed_data_items),
                len(delayed_fixed_plastic_data_items),
                len(delayed_plastic_plastic_data_items))) > 0:
            ((delayed_fixed_fixed, delayed_fixed_plastic,
              delayed_plastic_plastic),
             (delayed_ff_size, delayed_fp_size,
              delayed_pp_size)) = self._convert_data(
                delayed_fixed_fixed_data_items,
                delayed_fixed_plastic_data_items,
                delayed_plastic_plastic_data_items,
                pre_vertex_slice.n_atoms * n_stages)
            del delayed_fixed_fixed_data_items
            del delayed_fixed_plastic_data_items
            del delayed_plastic_plastic_data_items

            # Create the rows with the headers
            items_to_join = [delayed_pp_size, delayed_plastic_plastic,
                             delayed_ff_size, delayed_fp_size,
                             delayed_fixed_fixed, delayed_fixed_plastic]
            delayed_rows = [numpy.concatenate(items)
                            for items in zip(*items_to_join)]
            del delayed_fixed_fixed, delayed_fixed_plastic
            del delayed_plastic_plastic

            # Pad the rows to make them all the same length as the biggest
            row_lengths = [row.size for row in delayed_rows]
            max_length = max(row_lengths) - _N_HEADER_WORDS
            max_delayed_row_length = max_length
            if max_length > 0:
                max_length = population_table.get_allowed_row_length(
                    max_length)
                delayed_row_data = numpy.concatenate([numpy.pad(
                    row, (0, max_length - (row.size - _N_HEADER_WORDS)),
                    mode="constant", constant_values=0x11223344)
                    for row in delayed_rows])

        return (row_data, max_row_length, delayed_row_data,
                max_delayed_row_length, delayed_source_ids, stages)
