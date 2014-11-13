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
        
        if hasattr(self.delays, '__iter__'):
            iter(self.delays)
        else:
            self.delays = np.array([self.delays])
        
        if hasattr(self.weights, '__iter__'):
            iter(self.weights)
        else:
            self.weights = np.array([self.weights])
            
    def __str__(self):
        return "[Indices: {}, Weights: {}, Delays: {}, Types: {}]"\
            .format(self.target_indices, self.weights, self.delays,
                    self.synapse_types)
    
    def __repr__(self):
        return self.__str__()
    
    def append(self, row, lo_atom=0, min_delay=0):
        """
        Appends another row to this one
        If lo_atom is not None, lo_atom is added to each target index before
        appending
        If min_delay is not None, min_delay is added to each delay before
        appending
        """
        if len(self.target_indices) == 0:
            self.target_indices = row.target_indices + lo_atom
            self.weights = row.weights
            self.delays = row.delays + min_delay
            self.synapse_types = row.synapse_types
        else:
            np.append(self.target_indices, row.target_indices + lo_atom)
            np.append(self.weights, row.weights)
            np.append(self.delays, row.delays + min_delay)
            np.append(self.synapse_types, row.synapse_types)
        
            sort_indices = np.lexsort((self.target_indices, self.weights,
                                       self.delays, self.synapse_types))
            self.target_indices = self.target_indices[sort_indices]
            self.weights = self.weights[sort_indices]
            self.delays = self.delays[sort_indices]
            self.synapse_types = self.synapse_types[sort_indices]
        
    def get_n_connections(self, n_atoms=None):
        """
        Returns the number of connections in the row
        """
        if n_atoms is None:
            return self.target_indices.size
        
        mask = ((self.target_indices >= 0)
                & (self.target_indices <= n_atoms))
        x = self.target_indices[mask]
        return self.target_indices[mask].size
    
    def get_min_delay(self):
        """
        Returns the minimum delay in the row
        """
        if len(self.delays) == 0:
            return 0
        return np.amin(self.delays)
    
    def get_max_delay(self):
        """
        Returns the maximum delay in the row
        """
        if len(self.delays) == 0:
            return 0
        return np.amax(self.delays)
    
    def get_sub_row_by_atom(self, lo_atom, hi_atom):
        """
        Returns a subset of the row so that only connections to atoms between
        lo_atom and hi_atom (inclusive) are considered
        """
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
        mask = ((self.delays >= lo_delay) & (self.delays <= hi_delay))
        return type(self)(self.target_indices[mask], self.weights[mask],
                          self.delays[mask] - lo_delay,
                          self.synapse_types[mask])
        
    def get_max_weight(self):
        """
        Return the maximum weight in this row
        """
        if len(self.weights) == 0:
            return 0
        return np.amax(np.abs(self.weights))

    def get_min_weight(self):
        """
        Return the minimum weight in this row
        """
        if len(self.weights) == 0:
            return 0
        return np.amin(np.abs(self.weights))

    def flip_weights(self):
        """
        flips the weights from positive to engative and visa verse.
        """
        self.weights *= -1
