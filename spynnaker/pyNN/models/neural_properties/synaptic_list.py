import operator


class SynapticList(object):

    def __init__(self, synaptic_rows):
        """
        Creates a list of synaptic rows
        """
        self._synaptic_rows = synaptic_rows

    def get_max_n_connections(
            self, vertex_slice=None, lo_delay=None, hi_delay=None):
        """
        Return the maximum number of connections in the rows
        """
        return max(map(operator.methodcaller(
            'get_n_connections', vertex_slice, lo_delay, hi_delay),
            self._synaptic_rows))

    def get_min_delay(self):
        """
        Return the minimum and maximum delays in the rows
        """
        if len(self._synaptic_rows) == 0:
            return 0
        min_delay = min(map(operator.methodcaller('get_min_delay'),
                            self._synaptic_rows))
        return min_delay

    def get_max_delay(self):
        """
        Return the minimum and maximum delays in the rows
        """
        if len(self._synaptic_rows) == 0:
            return 0
        max_delay = max(map(operator.methodcaller('get_max_delay'),
                            self._synaptic_rows))
        return max_delay

    def get_max_weight(self):
        """
        Return the maximum weight in the rows
        """
        return max(map(operator.methodcaller('get_max_weight'),
                       self._synaptic_rows))

    def get_min_weight(self):
        """
        Return the minumum weight in the rows
        """
        return min(map(operator.methodcaller('get_min_weight'),
                       self._synaptic_rows))

    def sum_weights(self, sum_arrays):
        """
        Sums the weights going into each post-synaptic
        neuron on a per-synapse type basis
        """
        # **TODO** numpyify
        for row in self._synaptic_rows:
            for i, w, s in zip(row.target_indices, row.weights,
                               row.synapse_types):
                sum_arrays[s][i] += abs(w)

    def max_weights(self, max_arrays):
        for row in self._synaptic_rows:
            for w, s in zip(row.weights, row.synapse_types):
                max_arrays[s] = max(max_arrays[s], abs(w))

    def sum_square_weights(self, sum_arrays):
        """
        Sums the square of the weights going into each post-synaptic
        neuron on a per-synapse type basis
        """
        for row in self._synaptic_rows:
            for i, w, s in zip(row.target_indices, row.weights,
                               row.synapse_types):
                sum_arrays[s][i] += w * w

    def sum_fixed_weight(self, sum_arrays, fixed_weight):
        """
        Sums the weights going into each post-synaptic neuron,
        Assuming each pre-synaptic neuron applies a fixed
        Weight - used with a maximum weight provided by an STDP rule
        """
        # **TODO** numpyify
        for row in self._synaptic_rows:
            for i, s in zip(row.target_indices, row.synapse_types):
                sum_arrays[s][i] += fixed_weight

    def sum_n_connections(self, n_connections_arrays):
        """
        Sums the number of connections going into each post-synaptic neuron,
        on a per-synapse type basis
        """
        for row in self._synaptic_rows:
            for i, s in zip(row.target_indices, row.synapse_types):
                n_connections_arrays[s][i] += 1

    def is_connected(self, from_vertex_slice, to_vertex_slice):
        """
        Return true if the rows are connected for the specified range of
        incoming and outgoing atoms
        """
        for row in self._synaptic_rows[
                from_vertex_slice.lo_atom:from_vertex_slice.hi_atom + 1]:
            if row.get_n_connections(vertex_slice=to_vertex_slice) > 0:
                return True
        return False

    def get_atom_sublist(self, from_vertex_slice, to_vertex_slice):
        """
        Return a list of rows each of which represents only the information
        for atoms between lo_atom and hi_atom (inclusive)
        """
        return map(operator.methodcaller(
            'get_sub_row_by_atom', to_vertex_slice.lo_atom,
            to_vertex_slice.hi_atom),
            self._synaptic_rows[from_vertex_slice.lo_atom:
                                from_vertex_slice.hi_atom + 1])

    def get_delay_sublist(self, min_delay, max_delay):
        """
        Return a list of rows each of which represents only the information
        for atoms with delays between min_delay and max_delay (inclusive)
        """
        return map(operator.methodcaller('get_sub_row_by_delay', min_delay,
                                         max_delay),
                   self._synaptic_rows)

    def create_atom_sublist(self, from_vertex_slice, to_vertex_slice):
        """
        Create a sub list of this list which contains only atoms
        between lo_atom and hi_atom (inclusive)
        """
        return SynapticList(self.get_atom_sublist(from_vertex_slice,
                                                  to_vertex_slice))

    def create_delay_sublist(self, min_delay, max_delay):
        """
        Create a sub list of this list which contains only atoms with delays
        between min_delay and max_delay (inclusive)
        """
        return SynapticList(self.get_delay_sublist(min_delay, max_delay))

    def get_rows(self):
        """
        Return the rows to be written
        """
        return self._synaptic_rows

    def get_n_rows(self):
        """
        Return the number of rows
        """
        return len(self._synaptic_rows)

    def flip_weights(self):
        """
        flips the weights of each row from postive to negative and visa versa
        """
        for _ in self._synaptic_rows:
            map(operator.methodcaller('flip_weights'), self._synaptic_rows)

    def append(self, synapse_list):
        """
        Appends a synapse list to the end of this one
        """
        self._synaptic_rows.extend(synapse_list.synapticRows)

    def ranges(self):
        """
        Get the ranges of the current synaptic rows (start and end slice)
        """
        return [slice(0, len(row.target_indices))
                for row in self._synaptic_rows]

    def merge(self, synapse_list):
        """
        Merge the synapse list with this one - must have the same number of
        rows
        """
        if len(self._synaptic_rows) != len(synapse_list._synaptic_rows):
            raise Exception("Cannot merge lists as they have a different"
                            " number of rows")
        ranges = list()
        for row, new_row in zip(self._synaptic_rows,
                                synapse_list._synaptic_rows):
            start_offset = len(row.target_indices)
            row.append(new_row)
            ranges.append(slice(start_offset, len(row.target_indices)))
        return ranges

    def __str__(self):
        return "synaptic list containing {} entries which are {}"\
            .format(len(self._synaptic_rows), self._synaptic_rows)
