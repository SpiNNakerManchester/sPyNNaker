import numpy
import math

from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neuron.synapse_dynamics\
    .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
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

    def _n_words(self, n_bytes):
        return math.ceil(float(n_bytes) / 4.0)

    def get_sdram_usage_in_bytes(
            self, synapse_info, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table):

        # Find the maximum row length - i.e. the maximum number of bytes
        # that will be needed by any row for both rows with delay extensions
        # and rows without
        max_delay_supported = self.get_maximum_delay_supported_in_ms()
        max_delay = max_delay_supported * (n_delay_stages + 1)

        # delay point where delay extensions start
        min_delay_for_delay_extension = (
            max_delay_supported + numpy.finfo(numpy.double).tiny)

        # row length for the undelayed synaptic matrix
        max_undelayed_row_length = synapse_info.connector\
            .get_n_connections_from_pre_vertex_maximum(
                n_pre_slices, pre_slice_index, n_post_slices,
                post_slice_index, pre_vertex_slice, post_vertex_slice,
                0, max_delay_supported)

        # determine the max row length in the delay extension
        max_delayed_row_length = 0
        if n_delay_stages > 0:
            max_delayed_row_length = synapse_info.connector\
                .get_n_connections_from_pre_vertex_maximum(
                    n_pre_slices, pre_slice_index, n_post_slices,
                    post_slice_index, pre_vertex_slice, post_vertex_slice,
                    min_delay_for_delay_extension, max_delay)

        # Get the row sizes
        dynamics = synapse_info.synapse_dynamics
        undelayed_size = 0
        delayed_size = 0
        if isinstance(dynamics, AbstractStaticSynapseDynamics):
            undelayed_size = dynamics.get_n_words_for_static_connections(
                max_undelayed_row_length)
            delayed_size = dynamics.get_n_words_for_static_connections(
                max_delayed_row_length)
        else:
            undelayed_size = dynamics.get_n_words_for_plastic_connections(
                max_undelayed_row_length)
            delayed_size = dynamics.get_n_words_for_plastic_connections(
                max_delayed_row_length)

        # Adjust for the allowed row lengths from the population table
        undelayed_max_bytes = population_table.get_allowed_row_length(
            undelayed_size) * 4
        delayed_max_bytes = population_table.get_allowed_row_length(
            delayed_size) * 4

        # Add on the header words and multiply by the number of rows in the
        # block
        n_bytes_undelayed = 0
        if undelayed_max_bytes > 0:
            n_bytes_undelayed = (
                ((_N_HEADER_WORDS * 4) + undelayed_max_bytes) *
                pre_vertex_slice.n_atoms)
        n_bytes_delayed = 0
        if delayed_max_bytes > 0:
            n_bytes_delayed = (
                ((_N_HEADER_WORDS * 4) + delayed_max_bytes) *
                pre_vertex_slice.n_atoms * n_delay_stages)
        return n_bytes_undelayed, n_bytes_delayed

    @staticmethod
    def _get_max_row_length_and_row_data(
            connections, row_indices, n_rows, post_vertex_slice,
            n_synapse_types, population_table, synapse_dynamics):

        ff_data, ff_size = None, None
        fp_data, pp_data, fp_size, pp_size = None, None, None, None
        if isinstance(synapse_dynamics, AbstractStaticSynapseDynamics):

            # Get the static data
            ff_data, ff_size = synapse_dynamics.get_static_synaptic_data(
                connections, row_indices, n_rows, post_vertex_slice,
                n_synapse_types)

            # Blank the plastic data
            fp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            pp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            fp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]
            pp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]
        else:

            # Blank the static data
            ff_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            ff_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]

            # Get the plastic data
            fp_data, pp_data, fp_size, pp_size = \
                synapse_dynamics.get_plastic_synaptic_data(
                    connections, row_indices, n_rows, post_vertex_slice,
                    n_synapse_types)

        # Add some padding
        row_lengths = [
            3 + pp_data[i].size + fp_data[i].size + ff_data[i].size
            for i in range(n_rows)]
        max_length = max(row_lengths) - _N_HEADER_WORDS
        max_row_length = population_table.get_allowed_row_length(max_length)
        padding = [
            numpy.zeros(
                max_row_length - (row_length - _N_HEADER_WORDS),
                dtype="uint32")
            for row_length in row_lengths]

        # Join the bits into rows
        items_to_join = [
            pp_size, pp_data, ff_size, fp_size, ff_data, fp_data, padding]
        rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
        row_data = numpy.concatenate(rows)

        # Return the data
        return max_row_length, row_data

    def get_synapses(
            self, synapse_info, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales):

        # Get delays in timesteps
        max_delay = self.get_maximum_delay_supported_in_ms()
        if max_delay is not None:
            max_delay *= (1000.0 / self._machine_time_step)

        # Get the actual connections
        connections = synapse_info.connector.create_synaptic_block(
            pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_info.synapse_type)

        # Convert delays to timesteps
        connections["delay"] = numpy.rint(
            connections["delay"] * (1000.0 / self._machine_time_step))

        # Scale weights
        connections["weight"] = (
            connections["weight"] *
            weight_scales[synapse_info.synapse_type])

        # Split the connections up based on the delays
        undelayed_connections = connections
        delayed_connections = None
        if max_delay is not None:
            plastic_delay_mask = (connections["delay"] <= max_delay)
            undelayed_connections = connections[
                numpy.where(plastic_delay_mask)]
            delayed_connections = connections[
                numpy.where(~plastic_delay_mask)]
        else:
            delayed_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        del connections

        # Get the data for the connections
        row_data = numpy.zeros(0, dtype="uint32")
        max_row_length = 0
        if len(undelayed_connections) > 0:

            # Get which row each connection will go into
            undelayed_row_indices = (
                undelayed_connections["source"] - pre_vertex_slice.lo_atom)
            max_row_length, row_data = self._get_max_row_length_and_row_data(
                undelayed_connections, undelayed_row_indices,
                pre_vertex_slice.n_atoms, post_vertex_slice, n_synapse_types,
                population_table, synapse_info.synapse_dynamics)

            del undelayed_row_indices
        del undelayed_connections

        # Get the data for the delayed connections
        delayed_row_data = numpy.zeros(0, dtype="uint32")
        max_delayed_row_length = 0
        stages = numpy.zeros(0)
        delayed_source_ids = numpy.zeros(0)
        if len(delayed_connections) > 0:

            # Get the delay stages and which row each delayed connection will
            # go into
            stages = numpy.floor((numpy.round(
                delayed_connections["delay"] - 1.0)) / max_delay)
            delayed_row_indices = (
                (delayed_connections["source"] - pre_vertex_slice.lo_atom) +
                ((stages - 1) * pre_vertex_slice.n_atoms))
            delayed_connections["delay"] -= max_delay * stages
            delayed_source_ids = (
                delayed_connections["source"] - pre_vertex_slice.lo_atom)

            # Get the data
            max_delayed_row_length, delayed_row_data = \
                self._get_max_row_length_and_row_data(
                    delayed_connections, delayed_row_indices,
                    pre_vertex_slice.n_atoms * n_delay_stages,
                    post_vertex_slice, n_synapse_types, population_table,
                    synapse_info.synapse_dynamics)
            del delayed_row_indices
        del delayed_connections

        return (row_data, max_row_length, delayed_row_data,
                max_delayed_row_length, delayed_source_ids, stages)

    @staticmethod
    def _get_static_data(row_data, dynamics):
        n_rows = row_data.shape[0]
        ff_size = row_data[:, 1]
        ff_words = dynamics.get_n_static_words_per_row(ff_size)
        ff_start = _N_HEADER_WORDS
        ff_end = ff_start + ff_words
        return (
            ff_size,
            [row_data[row, ff_start:ff_end[row]] for row in range(n_rows)])

    @staticmethod
    def _get_plastic_data(row_data, dynamics):
        n_rows = row_data.shape[0]
        pp_size = row_data[:, 0]
        pp_words = dynamics.get_n_plastic_plastic_words_per_row(pp_size)
        fp_size = row_data[numpy.arange(n_rows), pp_words + 2]
        fp_words = dynamics.get_n_fixed_plastic_words_per_row(fp_size)
        fp_start = pp_size + _N_HEADER_WORDS
        fp_end = fp_start + fp_words
        return (
            pp_size,
            [row_data[row, 1:pp_words[row] + 1] for row in range(n_rows)],
            fp_size,
            [row_data[row, fp_start[row]:fp_end[row]] for row in range(n_rows)]
        )

    def read_synapses(
            self, synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            weight_scales, data, delayed_data, n_delay_stages):

        # Translate the data into rows
        row_data = None
        delayed_row_data = None
        row_stage = None
        connection_min_delay = None
        connection_source_extra = None
        if data is not None and len(data) > 0:
            row_data = numpy.frombuffer(data, dtype="<u4").reshape(
                -1, (max_row_length + _N_HEADER_WORDS))
        if delayed_data is not None and len(delayed_data) > 0:
            delayed_row_data = numpy.frombuffer(
                delayed_data, dtype="<u4").reshape(
                    -1, (delayed_max_row_length + _N_HEADER_WORDS))

        dynamics = synapse_info.synapse_dynamics
        connections = list()
        if isinstance(dynamics, AbstractStaticSynapseDynamics):

            # Read static data
            if row_data is not None and len(row_data) > 0:
                ff_size, ff_data = self._get_static_data(row_data, dynamics)
                undelayed_connections = dynamics.read_static_synaptic_data(
                    post_vertex_slice, n_synapse_types, ff_size, ff_data)
                undelayed_connections["source"] += pre_vertex_slice.lo_atom
                connections.append(undelayed_connections)
            if delayed_row_data is not None and len(delayed_row_data) > 0:
                ff_size, ff_data = self._get_static_data(
                    delayed_row_data, dynamics)
                delayed_connections = dynamics.read_static_synaptic_data(
                    post_vertex_slice, n_synapse_types, ff_size, ff_data)

                # Use the row index to work out the actual delay and source
                n_synapses = dynamics.get_n_synapses_in_rows(ff_size)
                row_stage = numpy.array([
                    (i / pre_vertex_slice.n_atoms)
                    for i in range(len(n_synapses))], dtype="uint32")
                row_min_delay = (row_stage + 1) * 16
                connection_min_delay = numpy.concatenate([
                    numpy.repeat(row_min_delay[i], n_synapses[i])
                    for i in range(len(n_synapses))])
                connection_source_extra = numpy.concatenate([
                    numpy.repeat(
                        row_stage[i] * pre_vertex_slice.n_atoms, n_synapses[i])
                    for i in range(len(n_synapses))])

                delayed_connections["source"] -= connection_source_extra
                delayed_connections["source"] += pre_vertex_slice.lo_atom
                delayed_connections["delay"] += connection_min_delay
                connections.append(delayed_connections)

        else:

            # Read plastic data
            if row_data is not None:
                pp_size, pp_data, fp_size, fp_data = self._get_plastic_data(
                    row_data, dynamics)
                undelayed_connections = dynamics.read_plastic_synaptic_data(
                    post_vertex_slice, n_synapse_types, pp_size, pp_data,
                    fp_size, fp_data)
                undelayed_connections["source"] += pre_vertex_slice.lo_atom
                connections.append(undelayed_connections)

            if delayed_row_data is not None:
                pp_size, pp_data, fp_size, fp_data = self._get_plastic_data(
                    delayed_row_data, dynamics)
                delayed_connections = dynamics.read_plastic_synaptic_data(
                    post_vertex_slice, n_synapse_types, pp_size, pp_data,
                    fp_size, fp_data)

                # Use the row index to work out the actual delay and source
                n_synapses = dynamics.get_n_synapses_in_rows(pp_size, fp_size)
                row_stage = numpy.array([
                    (i / pre_vertex_slice.n_atoms)
                    for i in range(len(n_synapses))], dtype="uint32")
                row_min_delay = (row_stage + 1) * 16
                connection_min_delay = numpy.concatenate([
                    numpy.repeat(row_min_delay[i], n_synapses[i])
                    for i in range(len(n_synapses))])
                connection_source_extra = numpy.concatenate([
                    numpy.repeat(
                        row_stage[i] * pre_vertex_slice.n_atoms, n_synapses[i])
                    for i in range(len(n_synapses))])

                delayed_connections["source"] -= connection_source_extra
                delayed_connections["source"] += pre_vertex_slice.lo_atom
                delayed_connections["delay"] += connection_min_delay
                connections.append(delayed_connections)

        # Join the connections into a single list
        if len(connections) > 0:
            connections = numpy.concatenate(connections)

            # Return the delays values to milliseconds
            connections["delay"] = (
                connections["delay"] / (1000.0 / self._machine_time_step))

            # Undo the weight scaling
            connections["weight"] = (
                connections["weight"] /
                weight_scales[synapse_info.synapse_type])
        else:
            connections = numpy.zeros(
                0, dtype=AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE)

        # Return the connections
        return connections

    def get_block_n_bytes(self, max_row_length, n_rows):
        return ((_N_HEADER_WORDS + max_row_length) * 4) * n_rows
