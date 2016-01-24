import numpy
import math
from collections import defaultdict

from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neuron.synapse_dynamics\
    .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from spynnaker.pyNN.models.neuron.synapse_io.abstract_synapse_io \
    import AbstractSynapseIO

_N_HEADER_WORDS = 3


class _ConnectorData(object):
    """ Private data that is stored during synapse generation to make the\
        retrieval of information possible
    """

    def __init__(self):
        self._undelayed_row_slices_by_pre_post_vertex_slices = defaultdict(
            lambda: None)
        self._delayed_row_slices_by_pre_post_vertex_slices = defaultdict(
            lambda: None)

    def set_undelayed_row_slices(
            self, pre_vertex_slice, post_vertex_slice, slices):
        self._undelayed_row_slices_by_pre_post_vertex_slices[
            (pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom,
             post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)] = slices

    def set_delayed_row_slices(
            self, pre_vertex_slice, post_vertex_slice, slices):
        self._delayed_row_slices_by_pre_post_vertex_slices[
            (pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom,
             post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)] = slices

    def get_undelayed_row_slices(self, pre_vertex_slice, post_vertex_slice):
        return self._undelayed_row_slices_by_pre_post_vertex_slices[
            (pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom,
             post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)]

    def get_delayed_row_slices(self, pre_vertex_slice, post_vertex_slice):
        return self._delayed_row_slices_by_pre_post_vertex_slices[
            (pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom,
             post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)]


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
        self._connector_data = defaultdict(_ConnectorData)
        self._plastic_synapse_dynamics = dict()
        self._static_synapse_dynamics = dict()

    def get_maximum_delay_supported_in_ms(self):

        # There are 16 slots, one per time step
        return 16 * (self._machine_time_step / 1000.0)

    def _n_words(self, n_bytes):
        return math.ceil(float(n_bytes) / 4.0)

    def get_sdram_usage_in_bytes(
            self, edge, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table):

        # Find the maximum row length - i.e. the maximum number of bytes
        # that will be needed by any row for both rows with delay extensions
        # and rows without
        total_plastic_undelayed_row_length = 0
        total_static_undelayed_row_length = 0
        total_plastic_delayed_row_length = 0
        total_static_delayed_row_length = 0
        max_delay_supported = self.get_maximum_delay_supported_in_ms()
        next_max_delay_supported = (
            max_delay_supported + numpy.finfo(numpy.double).tiny)
        max_delay = max_delay_supported * (n_delay_stages + 1)

        plastic_synapse_dynamics = None
        static_synapse_dynamics = None

        for synapse_info in edge.synapse_information:
            max_undelayed_row_length = synapse_info.connector\
                .get_n_connections_from_pre_vertex_maximum(
                    n_pre_slices, pre_slice_index, n_post_slices,
                    post_slice_index, pre_vertex_slice, post_vertex_slice,
                    0, max_delay_supported)
            max_delayed_row_length = 0
            if n_delay_stages > 0:
                max_delayed_row_length = synapse_info.connector\
                    .get_n_connections_from_pre_vertex_maximum(
                        n_pre_slices, pre_slice_index, n_post_slices,
                        post_slice_index, pre_vertex_slice, post_vertex_slice,
                        next_max_delay_supported, max_delay)

            dynamics = synapse_info.synapse_dynamics

            if isinstance(dynamics, AbstractStaticSynapseDynamics):
                static_synapse_dynamics = dynamics
                total_static_undelayed_row_length += max_undelayed_row_length
                total_static_delayed_row_length += max_delayed_row_length
            else:
                plastic_synapse_dynamics = dynamics
                total_plastic_undelayed_row_length += max_undelayed_row_length
                total_plastic_delayed_row_length += max_delayed_row_length

        # Get the static row sizes
        undelayed_static_size = 0
        delayed_static_size = 0
        if static_synapse_dynamics is not None:
            undelayed_static_size = static_synapse_dynamics\
                .get_n_words_for_static_connections(
                    total_static_undelayed_row_length)
            delayed_static_size = static_synapse_dynamics\
                .get_n_words_for_static_connections(
                    total_static_delayed_row_length)

        # Get the plastic row sizes
        undelayed_plastic_size = 0
        delayed_plastic_size = 0
        if plastic_synapse_dynamics is not None:
            undelayed_plastic_size = plastic_synapse_dynamics\
                .get_n_words_for_plastic_connections(
                    total_plastic_undelayed_row_length)
            delayed_plastic_size = plastic_synapse_dynamics\
                .get_n_words_for_plastic_connections(
                    total_plastic_delayed_row_length)

        # Adjust for the allowed row lengths from the population table
        undelayed_max_bytes = population_table.get_allowed_row_length(
            undelayed_static_size + undelayed_plastic_size) * 4
        delayed_max_bytes = population_table.get_allowed_row_length(
            delayed_static_size + delayed_plastic_size) * 4

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
        return (n_bytes_undelayed, n_bytes_delayed)

    @staticmethod
    def _get_max_row_length_and_row_data(
            static_connections, plastic_connections, static_row_indices,
            plastic_row_indices, n_rows, post_vertex_slice, n_synapse_types,
            population_table, static_synapse_dynamics,
            plastic_synapse_dynamics):

        # Get the static data
        ff_data, ff_size = None, None
        if static_synapse_dynamics is not None:
            ff_data, ff_size = \
                static_synapse_dynamics.get_static_synaptic_data(
                    static_connections, static_row_indices, n_rows,
                    post_vertex_slice, n_synapse_types)
        else:
            ff_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            ff_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]

        # Get the plastic data
        fp_data, pp_data, fp_size, pp_size = None, None, None, None
        if plastic_synapse_dynamics is not None:
            fp_data, pp_data, fp_size, pp_size = \
                plastic_synapse_dynamics.get_plastic_synaptic_data(
                    plastic_connections, plastic_row_indices, n_rows,
                    post_vertex_slice, n_synapse_types)
        else:
            fp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            pp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
            fp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]
            pp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]

        # Join the bits into rows
        items_to_join = [pp_size, pp_data, ff_size, fp_size, ff_data, fp_data]
        rows = [numpy.concatenate(items) for items in zip(*items_to_join)]

        # Make all the rows the same length
        row_lengths = [row.size for row in rows]
        max_row_length = max(row_lengths) - _N_HEADER_WORDS
        max_length = population_table.get_allowed_row_length(max_row_length)
        row_data = numpy.concatenate([
            numpy.pad(
                row, (0, max_length - (row.size - _N_HEADER_WORDS)),
                mode="constant", constant_values=0x11223344)
            for row in rows])

        # Return the data
        return max_row_length, row_data

    def _update_connectors(
            self, synapse_information, plastic_connections,
            plastic_row_indices, static_connections, static_row_indices,
            n_rows, pre_vertex_slice, post_vertex_slice, delayed):

        # Store the connector data for each connector
        plastic_connector_index_rows = [
            plastic_connections["connector_index"][plastic_row_indices == i]
            for i in xrange(n_rows)]
        static_connector_index_rows = [
            static_connections["connector_index"][static_row_indices == i]
            for i in xrange(n_rows)]

        connector_index = 0
        for synapse_info in synapse_information:

            # Work out if this is a static or plastic connector
            index_rows = None
            if isinstance(
                    synapse_info.synapse_dynamics,
                    AbstractStaticSynapseDynamics):
                index_rows = static_connector_index_rows
            else:
                index_rows = plastic_connector_index_rows

            # Get the slices for each row of the matrix for this connector
            slices = [
                numpy.where(row == connector_index)[0] for row in index_rows]

            # Update the synapse io data in the synapse info
            if not delayed:
                self._connector_data[synapse_info].set_undelayed_row_slices(
                    pre_vertex_slice, post_vertex_slice, slices)
            else:
                self._connector_data[synapse_info].set_delayed_row_slices(
                    pre_vertex_slice, post_vertex_slice, slices)
            connector_index += 1

    def get_synapses(
            self, edge, n_pre_slices, pre_slice_index,
            n_post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales):

        # Get delays in timesteps
        max_delay = self.get_maximum_delay_supported_in_ms()
        if max_delay is not None:
            max_delay = max_delay * (1000.0 / self._machine_time_step)

        # Gather the connectivity data by plastic and non-plastic
        # (the assumption is that there is only one plastic synapse
        #  dynamics type)
        all_plastic_connections = list()
        all_static_connections = list()
        connector_index = 0
        plastic_synapse_dynamics = None
        static_synapse_dynamics = None
        for synapse_info in edge.synapse_information:

            # Get the actual connections
            connections = synapse_info.connector.create_synaptic_block(
                n_pre_slices, pre_slice_index, n_post_slices,
                post_slice_index, pre_vertex_slice, post_vertex_slice,
                synapse_info.synapse_type, connector_index)

            if isinstance(
                    synapse_info.synapse_dynamics,
                    AbstractStaticSynapseDynamics):

                # Assume that it has been checked that all these are
                # as_same_as each other
                static_synapse_dynamics = synapse_info.synapse_dynamics
                all_static_connections.append(connections)
            else:

                # Assume that it has been checked that all these are
                # as_same_as each other
                plastic_synapse_dynamics = synapse_info.synapse_dynamics
                all_plastic_connections.append(connections)

            connector_index += 1
            del connections

        # Join the connections up
        plastic_connections = None
        if plastic_synapse_dynamics is not None:
            plastic_connections = numpy.concatenate(all_plastic_connections)
        else:
            plastic_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        static_connections = None
        if static_synapse_dynamics is not None:
            static_connections = numpy.concatenate(all_static_connections)
        else:
            static_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Convert delays to timesteps
        plastic_connections["delay"] = numpy.rint(
            plastic_connections["delay"] * (1000.0 / self._machine_time_step))
        static_connections["delay"] = numpy.rint(
            static_connections["delay"] * (1000.0 / self._machine_time_step))

        # Scale weights
        plastic_connections["weight"] = (
            plastic_connections["weight"] *
            weight_scales[plastic_connections["synapse_type"]])
        static_connections["weight"] = (
            static_connections["weight"] *
            weight_scales[static_connections["synapse_type"]])

        # Split the connections up based on the delays
        undelayed_plastic_connections = plastic_connections
        undelayed_static_connections = static_connections
        delayed_plastic_connections = None
        delayed_static_connections = None
        if max_delay is not None:
            plastic_delay_mask = (plastic_connections["delay"] <= max_delay)
            undelayed_plastic_connections = plastic_connections[
                numpy.where(plastic_delay_mask)]
            delayed_plastic_connections = plastic_connections[
                numpy.where(~plastic_delay_mask)]

            static_delay_mask = (static_connections["delay"] <= max_delay)
            undelayed_static_connections = static_connections[
                numpy.where(static_delay_mask)]
            delayed_static_connections = static_connections[
                numpy.where(~static_delay_mask)]
        else:
            delayed_plastic_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
            delayed_static_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        del plastic_connections, static_connections

        # Get the data for the connections
        row_data = numpy.zeros(0, dtype="uint32")
        max_row_length = 0
        if sum((len(undelayed_plastic_connections),
                len(undelayed_static_connections))) > 0:

            # Get which row each connection will go into
            undelayed_plastic_row_indices = (
                undelayed_plastic_connections["source"] -
                pre_vertex_slice.lo_atom)
            undelayed_static_row_indices = (
                undelayed_static_connections["source"] -
                pre_vertex_slice.lo_atom)
            max_row_length, row_data = self._get_max_row_length_and_row_data(
                undelayed_static_connections, undelayed_plastic_connections,
                undelayed_static_row_indices, undelayed_plastic_row_indices,
                pre_vertex_slice.n_atoms, post_vertex_slice, n_synapse_types,
                population_table, static_synapse_dynamics,
                plastic_synapse_dynamics)

            self._update_connectors(
                edge.synapse_information, undelayed_plastic_connections,
                undelayed_plastic_row_indices, undelayed_static_connections,
                undelayed_static_row_indices, pre_vertex_slice.n_atoms,
                pre_vertex_slice, post_vertex_slice, delayed=False)

            del undelayed_plastic_row_indices, undelayed_static_row_indices
        del undelayed_plastic_connections, undelayed_static_connections

        # Get the data for the delayed connections
        delayed_row_data = numpy.zeros(0, dtype="uint32")
        max_delayed_row_length = 0
        stages = numpy.zeros(0)
        delayed_source_ids = numpy.zeros(0)
        if sum((len(delayed_plastic_connections),
                len(delayed_static_connections))) > 0:

            # Get the delay stages and which row each delayed connection will
            # go into
            plastic_stages = numpy.floor((numpy.round(
                delayed_plastic_connections["delay"] - 1.0)) / max_delay)
            static_stages = numpy.floor((numpy.round(
                delayed_static_connections["delay"] - 1.0)) / max_delay)
            delayed_plastic_row_indices = (
                (delayed_plastic_connections["source"] -
                 pre_vertex_slice.lo_atom) +
                ((plastic_stages - 1) * pre_vertex_slice.n_atoms))
            delayed_static_row_indices = (
                (delayed_static_connections["source"] -
                 pre_vertex_slice.lo_atom) +
                ((static_stages - 1) * pre_vertex_slice.n_atoms))
            delayed_plastic_connections["delay"] -= max_delay * plastic_stages
            delayed_static_connections["delay"] -= max_delay * static_stages
            delayed_plastic_source_ids = (
                delayed_plastic_connections["source"] -
                pre_vertex_slice.lo_atom)
            delayed_static_source_ids = (
                delayed_static_connections["source"] -
                pre_vertex_slice.lo_atom)

            # Get the data
            max_delayed_row_length, delayed_row_data = \
                self._get_max_row_length_and_row_data(
                    delayed_static_connections, delayed_plastic_connections,
                    delayed_static_row_indices, delayed_plastic_row_indices,
                    pre_vertex_slice.n_atoms * n_delay_stages,
                    post_vertex_slice, n_synapse_types, population_table,
                    static_synapse_dynamics, plastic_synapse_dynamics)

            self._update_connectors(
                edge.synapse_information, delayed_plastic_connections,
                delayed_plastic_row_indices, delayed_static_connections,
                delayed_static_row_indices,
                pre_vertex_slice.n_atoms * n_delay_stages, pre_vertex_slice,
                post_vertex_slice, delayed=True)

            # Get the stages and source ids
            stages = numpy.concatenate((plastic_stages, static_stages))
            delayed_source_ids = numpy.concatenate(
                (delayed_plastic_source_ids, delayed_static_source_ids))
            del delayed_plastic_row_indices, delayed_static_row_indices
            del plastic_stages, static_stages
            del delayed_plastic_source_ids, delayed_static_source_ids
        del delayed_plastic_connections, delayed_static_connections

        self._static_synapse_dynamics[edge] = static_synapse_dynamics
        self._plastic_synapse_dynamics[edge] = plastic_synapse_dynamics

        return (row_data, max_row_length, delayed_row_data,
                max_delayed_row_length, delayed_source_ids, stages)

    def _get_static_data(
            self, row_data, static_synapse_dynamics, plastic_synapse_dynamics):
        n_rows = row_data.shape[0]
        pp_size = None
        if plastic_synapse_dynamics is not None:
            pp_size = plastic_synapse_dynamics\
                .get_n_plastic_plastic_words_per_row(row_data[:, 0])
        else:
            pp_size = numpy.zeros(n_rows, dtype="uint32")
        ff_size = static_synapse_dynamics.get_n_static_words_per_row(
            row_data[numpy.arange(n_rows), pp_size + 1])
        ff_start = pp_size + _N_HEADER_WORDS
        ff_end = ff_start + ff_size
        return (
            ff_size,
            [row_data[row, ff_start[row]:ff_end[row]]
             for row in range(n_rows)])

    def _get_plastic_data(
            self, row_data, static_synapse_dynamics, plastic_synapse_dynamics):
        n_rows = row_data.shape[0]
        indices = numpy.arange(n_rows)
        pp_size = plastic_synapse_dynamics\
            .get_n_plastic_plastic_words_per_row(row_data[:, 0])
        ff_size = None
        if static_synapse_dynamics is not None:
            ff_size = static_synapse_dynamics.get_n_static_words_per_row(
                row_data[indices, pp_size + 1])
        else:
            ff_size = numpy.zeros(n_rows, dtype="uint32")
        fp_size = plastic_synapse_dynamics\
            .get_n_fixed_plastic_words_per_row(row_data[indices, pp_size + 2])
        fp_start = pp_size + ff_size + _N_HEADER_WORDS
        fp_end = fp_start + fp_size
        return (
            pp_size,
            [row_data[row, 1:pp_size[row] + 1]
             for row in range(n_rows)],
            fp_size,
            [row_data[row, fp_start[row]:fp_end[row]]
             for row in range(n_rows)])

    def read_synapses(
            self, edge, synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            weight_scales, data, delayed_data, n_delay_stages):

        # Get the connection indices for this slice
        connection_data = self._connector_data[synapse_info]
        undelayed_connection_indices = \
            connection_data.get_undelayed_row_slices(
                pre_vertex_slice, post_vertex_slice)
        delayed_connection_indices = \
            connection_data.get_delayed_row_slices(
                pre_vertex_slice, post_vertex_slice)
        static_synapse_dynamics = self._static_synapse_dynamics[edge]
        plastic_synapse_dynamics = self._plastic_synapse_dynamics[edge]

        # Use the row index to work out the actual delay and source
        row_stage = None
        connection_min_delay = None
        connection_source_extra = None
        if delayed_connection_indices is not None:
            row_stage = numpy.array([
                (i / pre_vertex_slice.n_atoms)
                for i in range(len(delayed_connection_indices))],
                dtype="uint32")
            row_min_delay = (row_stage + 1) * 16
            connection_min_delay = numpy.concatenate([
                numpy.repeat(
                    row_min_delay[i], len(delayed_connection_indices[i]))
                for i in range(len(delayed_connection_indices))])
            connection_source_extra = numpy.concatenate([
                numpy.repeat(
                    row_stage[i] * pre_vertex_slice.n_atoms,
                    len(delayed_connection_indices[i]))
                for i in range(len(delayed_connection_indices))])

        # Translate the data into rows
        row_data = None
        delayed_row_data = None
        if data is not None:
            row_data = numpy.frombuffer(data, dtype="<u4").reshape(
                -1, (max_row_length + _N_HEADER_WORDS))
        if delayed_data is not None:
            delayed_row_data = numpy.frombuffer(
                delayed_data, dtype="<u4").reshape(
                    -1, (delayed_max_row_length + _N_HEADER_WORDS))

        dynamics = synapse_info.synapse_dynamics
        connections = list()
        if isinstance(dynamics, AbstractStaticSynapseDynamics):

            # Read static data
            if undelayed_connection_indices is not None:
                ff_size, ff_data = self._get_static_data(
                    row_data, static_synapse_dynamics,
                    plastic_synapse_dynamics)
                undelayed_connections = dynamics.read_static_synaptic_data(
                    undelayed_connection_indices, post_vertex_slice,
                    n_synapse_types, ff_size, ff_data)
                undelayed_connections["source"] += pre_vertex_slice.lo_atom
                connections.append(undelayed_connections)
            if delayed_connection_indices is not None:
                ff_size, ff_data = self._get_static_data(
                    delayed_row_data, static_synapse_dynamics,
                    plastic_synapse_dynamics)
                delayed_connections = dynamics.read_static_synaptic_data(
                    delayed_connection_indices, post_vertex_slice,
                    n_synapse_types, ff_size, ff_data)
                delayed_connections["source"] -= connection_source_extra
                delayed_connections["source"] += pre_vertex_slice.lo_atom
                delayed_connections["delay"] += connection_min_delay
                connections.append(delayed_connections)

        else:

            # Read plastic data
            if undelayed_connection_indices is not None:
                pp_size, pp_data, fp_size, fp_data = self._get_plastic_data(
                    row_data, static_synapse_dynamics,
                    plastic_synapse_dynamics)
                connections.append(dynamics.read_plastic_synaptic_data(
                    undelayed_connection_indices, post_vertex_slice,
                    n_synapse_types, pp_size, pp_data, fp_size, fp_data))

            if delayed_connection_indices is not None:
                pp_size, pp_data, fp_size, fp_data = self._get_plastic_data(
                    delayed_row_data, static_synapse_dynamics,
                    plastic_synapse_dynamics)
                delayed_connections = dynamics.read_plastic_synaptic_data(
                    delayed_connection_indices, post_vertex_slice,
                    n_synapse_types, pp_size, pp_data, fp_size, fp_data)
                delayed_connections["source"] -= connection_source_extra
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
