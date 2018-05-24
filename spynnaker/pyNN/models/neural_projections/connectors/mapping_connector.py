import numpy
from .abstract_connector import AbstractConnector
from pacman.model.decorators.overrides import overrides
from .abstract_generate_connector_on_machine import \
    AbstractGenerateConnectorOnMachine, ConnectorIDs


class MappingConnector(AbstractGenerateConnectorOnMachine):
    """
    Where the pre- and postsynaptic populations have the same size, connect
    cell i in the presynaptic pynn_population.py to cell i in the postsynaptic
    pynn_population.py for all i.
    """

    def __init__(
            self, width, height, channel, height_bits, channel_bits=1,
            event_bits=0, safe=True, verbose=False):
        """
        """
        super(MappingConnector, self).__init__(self, safe, verbose)
        self._width = numpy.uint32(width)
        self._height = numpy.uint32(height)

        self._height_bits = numpy.uint32(height_bits)
        self._row_mask = numpy.uint32((1 << height_bits) - 1)
        self._channel_bits = numpy.uint32(channel_bits)
        self._channel_mask = numpy.uint32((1 << channel_bits) - 1)

        self._event_bits = numpy.uint32(event_bits)
        self._event_mask = numpy.uint32((1 << event_bits) - 1)

        self._chan_shift_bits = event_bits
        self._row_shift_bits = channel_bits + self._chan_shift_bits
        self._col_shift_bits = height_bits + self._row_shift_bits

        self._col_mask = (1 << (32 - self._row_shift_bits)) - 1

        self._channel = numpy.uint32(channel & self._channel_mask)

    def extreme_row(self, v_slice, op):
        ids = numpy.arange(
            v_slice.lo_atom, v_slice.hi_atom + 1, dtype='uint32')
        rows = numpy.bitwise_and(numpy.right_shift(ids, self._row_shift_bits),
                                 self._row_mask)
        if op == 'max':
            return rows.max()
        else:
            return rows.min()

    def extreme_col(self, v_slice, op):
        ids = numpy.arange(
            v_slice.lo_atom, v_slice.hi_atom + 1, dtype='uint32')
        cols = numpy.right_shift(ids, self._col_shift_bits)

        if op == 'max':
            return cols.max()
        else:
            return cols.min()

    def to_pre_id(self, row, col):
        row = numpy.bitwise_and(numpy.uint32(row), self._row_mask)
        col = numpy.bitwise_and(numpy.uint32(col), self._col_mask)
        pre_id = (
            numpy.left_shift(col, self._col_shift_bits) +
            numpy.left_shift(row, self._row_shift_bits) +
            numpy.left_shift(self._channel, self._chan_shift_bits))
        return numpy.uint32(pre_id)

    def in_pre_range(self, min_row, max_row, pre_slice):
        rows = numpy.repeat(numpy.arange(min_row, max_row + 1), self._width)
        cols = numpy.tile(numpy.arange(self._width), max_row - min_row + 1)

        ids = self.to_pre_id(rows, cols)
        pre_ids = numpy.arange(pre_slice.lo_atom, pre_slice.hi_atom + 1)
        matching = numpy.intersect1d(ids, pre_ids, assume_unique=True)
        return matching

    def to_post_ids(self, indices):
        rows = numpy.bitwise_and(
            numpy.right_shift(indices, self._row_shift_bits), self._row_mask)
        cols = numpy.bitwise_and(
            numpy.right_shift(indices, self._col_shift_bits), self._col_mask)

        return (rows*self._width + cols)

    def _nconns(self, pre_vertex_slice, post_vertex_slice):

        pre_min_row = self.extreme_row(pre_vertex_slice, 'min')
        pre_max_row = self.extreme_row(pre_vertex_slice, 'max')

        post_min_row = int(post_vertex_slice.lo_atom) // self._width
        post_max_row = int(post_vertex_slice.hi_atom) // self._width

        # print("\n")
        # print(pre_vertex_slice)
        # print(post_vertex_slice)
        # print("pre min %d > post max %d or pre max %d < post min %d == %s"%(
        #       pre_min_row, post_max_row, pre_max_row, post_min_row,
        #       pre_min_row > post_max_row or pre_max_row < post_min_row))

        if pre_min_row > post_max_row or pre_max_row < post_min_row:
            return 0

        max_row = min(pre_max_row, post_max_row)
        min_row = max(pre_min_row, post_min_row)

        # print("rows: min %d, max %d, n %d"%(min_row, max_row, n_rows))

        nids = self.in_pre_range(min_row, max_row, pre_vertex_slice).size
        # print("matching ids = %d"%nids)
        return nids

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, max((self._n_pre_neurons, self._n_post_neurons)))

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if self._nconns(pre_vertex_slice, post_vertex_slice) == 0:
            return 0

        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_delay_variance(self._delays, [connection_slice])

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        n_conns = int(self._nconns(pre_vertex_slice, post_vertex_slice) > 0)

        # print("in get_n_connections_from_pre_vertex_maximum")
        # print(n_conns)
        if n_conns == 0:
            return 0

        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))

        if min_delay is None or max_delay is None:
            return n_conns
        if isinstance(self._delays, self._random_number_class):
            return n_conns
        elif numpy.isscalar(self._delays):
            if self._delays >= min_delay and self._delays <= max_delay:
                return n_conns
            return 0
        else:
            connection_slice = slice(max_lo_atom, min_hi_atom + 1)
            slice_min_delay = min(self._delays[connection_slice])
            slice_max_delay = max(self._delays[connection_slice])
            if slice_min_delay >= min_delay and slice_max_delay <= max_delay:
                return n_conns
            return 0

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        # return min(self._nconns(pre_vertex_slice, post_vertex_slice),
        #            post_vertex_slice.n_atoms)
        if self._nconns(pre_vertex_slice, post_vertex_slice) > 0:
            return 1
        else:
            return 0

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if self._nconns(pre_vertex_slice, post_vertex_slice) == 0:
            return 0

        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))

        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_mean(self._weights, [connection_slice])

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = self._nconns(pre_vertex_slice, post_vertex_slice)
        if n_connections == 0:
            return 0

        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))

        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_maximum(
            self._weights, n_connections, [connection_slice])

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if self._nconns(pre_vertex_slice, post_vertex_slice) == 0:
            return 0

        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))

        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_variance(self._weights, [connection_slice])

    def generate_on_machine(self):
        return (self._gen_on_spinn and
                self._generate_lists_on_machine(self._weights) and
                self._generate_lists_on_machine(self._delays))

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):

        pre_min_row = self.extreme_row(pre_vertex_slice, 'min')
        pre_max_row = self.extreme_row(pre_vertex_slice, 'max')

        post_min_row = int(post_vertex_slice.lo_atom) // self._width
        post_max_row = int(post_vertex_slice.hi_atom) // self._width

        if pre_min_row > post_max_row or pre_max_row < post_min_row:
            return 0

        max_row = min(pre_max_row, post_max_row)
        min_row = max(pre_min_row, post_min_row)

        pre_indices = self.in_pre_range(min_row, max_row, pre_vertex_slice)

        n_connections = pre_indices.size

        if n_connections <= 0:
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        lo_atom = max(min_row*self._width, post_vertex_slice.lo_atom)
        hi_atom = min(max_row*self._width + self._width - 1,
                      post_vertex_slice.hi_atom)
        connection_slice = slice(lo_atom, hi_atom + 1)

        post_indices = self.to_post_ids(pre_indices)

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pre_indices
        block["target"] = post_indices
        block["weight"] = self._generate_weights(
            self._weights, n_connections, [connection_slice])
        block["delay"] = self._generate_delays(
            self._delays, n_connections, [connection_slice])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "MappingConnector"

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.MAPPING_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        return numpy.array([
            ((numpy.uint32(self._width) & 0xFFFF) << 16) |
            (numpy.uint32(self._height) & 0xFFFF),
            numpy.uint32(self._channel & 0xFF |
                         ((self._event_bits & 0xFF) << 8) |
                         ((self._channel_bits & 0xFF) << 16) |
                         ((self._height_bits & 0xFF) << 24))
            ], dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 8
