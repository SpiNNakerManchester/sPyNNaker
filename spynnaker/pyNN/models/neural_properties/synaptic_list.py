import operator


class SynapticList(object):
    
    def __init__(self, synaptic_rows):
        """
        Creates a list of synaptic rows
        """
        self._synaptic_rows = synaptic_rows
        
    def get_max_n_connections(self, vertex_slice=None):
        """
        Return the maximum number of connections in the rows
        """
        if vertex_slice is None:
            return max(map(operator.methodcaller(
                'get_n_connections', None), self._synaptic_rows))
        else:
            return max(map(operator.methodcaller(
                'get_n_connections', vertex_slice.lo_atom,
                vertex_slice.hi_atom), self._synaptic_rows))
    
    def get_min_max_delay(self):
        """
        Return the minimum and maximum delays in the rows
        """
        if len(self._synaptic_rows) == 0:
            return 0, 0
        min_delay = min(map(operator.methodcaller('get_min_delay'),
                            self._synaptic_rows))
        max_delay = max(map(operator.methodcaller('get_max_delay'),
                            self._synaptic_rows))
        return min_delay, max_delay
    
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
        
    def sum_weights(self, exc_sum_array, inh_sum_array):
        """
        Sums the positive weights of the rows into exc_sum_array, and the
        negative weights of the rows into inh_sum_array, each of which is an 
        array of numbers indexed by the target indices
        """
        for row in self._synaptic_rows:
            for i in range(0, len(row.target_indices)):
                index = row.target_indices[i]
                weight = row.weights[i]
                if weight > 0:
                    exc_sum_array[index] += weight
                else:
                    inh_sum_array[index] += abs(weight)
    
    def is_connected(self, from_vertex_slice, to_vertex_slice):
        """
        Return true if the rows are connected for the specified range of
        incoming and outgoing atoms
        """
        for row in self._synaptic_rows[from_vertex_slice.lo_atom:
                                       from_vertex_slice.hi_atom + 1]:
            if row.get_n_connections(to_vertex_slice.n_atoms) > 0:
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

    def __str__(self):
        return "synaptic list containing {} entries which are {}"\
            .format(len(self._synaptic_rows), self._synaptic_rows)