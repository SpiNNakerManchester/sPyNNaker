import numpy as np


class SynapseRowInfo(object):

    def __init__(self, target_indices, weights, delays_in_ticks,
                 synapse_types):
        """
        Creates a row of synapses
        """
        self.target_indices = np.asarray(target_indices, dtype='uint32')
        self.weights = np.asarray(weights, dtype='float')
        self.delays = np.asarray(delays_in_ticks, dtype='uint32')
        self.synapse_types = np.asarray(synapse_types, dtype='uint32')

    def append(self, row, lo_atom=0, min_delay=0):
        """
        Appends another row to this one
        If lo_atom is not None, lo_atom is added to each target index before
        appending
        If min_delay is not None, min_delay is added to each delay before
        appending
        """
        if self.target_indices.size == 0:
            self.target_indices = row.target_indices + lo_atom
            self.weights = row.weights
            self.delays = row.delays + min_delay
            self.synapse_types = row.synapse_types
        else:
            self.target_indices = np.append(self.target_indices,
                                            row.target_indices + lo_atom)
            self.weights = np.append(self.weights, row.weights)
            self.delays = np.append(self.delays, row.delays + min_delay)
            self.synapse_types = np.append(self.synapse_types,
                                           row.synapse_types)

    def __getitem__(self, index):
        """
        This is a python method to support slicing of a synaptic list

        :param index: the part of the slice to return.
        :return: a SynapseRowInfo
        """
        return SynapseRowInfo(self.target_indices[index], self.weights[index],
                              self.delays[index], self.synapse_types[index])

    def get_n_connections(self, vertex_slice=None, lo_delay=None,
                          hi_delay=None):
        """
        Returns the number of connections in the row
        """
        if self.target_indices.size == 0:
            return 0

        if vertex_slice is None and lo_delay is None and hi_delay is None:
            return self.target_indices.size

        if vertex_slice is not None and lo_delay is None and hi_delay is None:
            mask = ((self.target_indices >= vertex_slice.lo_atom)
                    & (self.target_indices <= vertex_slice.hi_atom))
            return np.sum(mask)

        if (vertex_slice is None and lo_delay is not None
                and hi_delay is not None):
            mask = ((self.delays >= lo_delay)
                    & (self.delays <= hi_delay))
            return np.sum(mask)

        mask = ((self.target_indices >= vertex_slice.lo_atom)
                & (self.target_indices <= vertex_slice.hi_atom)
                & (self.delays >= lo_delay) & (self.delays <= hi_delay))
        return np.sum(mask)

    def get_min_delay(self):
        """
        Returns the minimum delay in the row
        """
        if self.delays.size == 0:
            return 0
        return np.amin(self.delays)

    def get_max_delay(self):
        """
        Returns the maximum delay in the row
        """
        if self.delays.size == 0:
            return 0
        return np.amax(self.delays)

    def get_sub_row_by_atom(self, lo_atom, hi_atom):
        """
        Returns a subset of the row so that only connections to atoms between
        lo_atom and hi_atom (inclusive) are considered
        """
        if self.target_indices.size == 0:
            return type(self)([], [], [], [])
        mask = ((self.target_indices >= lo_atom)
                & (self.target_indices <= hi_atom))
        return type(self)(self.target_indices[mask] - lo_atom,
                          self.weights[mask], self.delays[mask],
                          self.synapse_types[mask])

    def get_sub_row_by_delay(self, lo_delay, hi_delay):
        """
        Returns a subset of the row so that only connections with delays
        between lo_delay and hi_delay (inclusive) are considered
        """
        if self.target_indices.size == 0:
            return type(self)([], [], [], [])
        mask = ((self.delays >= lo_delay) & (self.delays <= hi_delay))
        return type(self)(self.target_indices[mask], self.weights[mask],
                          self.delays[mask],
                          self.synapse_types[mask])

    def get_max_weight(self):
        """
        Return the maximum weight in this row
        """
        if self.weights.size == 0:
            return 0
        return np.amax(np.abs(self.weights))

    def get_min_weight(self):
        """
        Return the minimum weight in this row
        """
        if self.weights.size == 0:
            return 0
        return np.amin(np.abs(self.weights))

    def flip_weights(self):
        """
        flips the weights from positive to engative and visa verse.
        """
        self.weights *= -1
