class AbstractSynapseRowIo(object):
    
    def get_n_words(self, synapse_row, lo_atom=None, hi_atom=None):
        """
        Returns the total size of the fixed and plastic regions of the row in
        words
        """
        raise NotImplementedError

    def get_packed_fixed_fixed_region(self, synapse_row, weight_scale, 
                                      n_synapse_type_bits):
        """
        Gets the fixed part of the fixed region as an array of 32-bit words
        """
        raise NotImplementedError

    def get_packed_fixed_plastic_region(self, synapse_row, weight_scale,
                                        n_synapse_type_bits):
        """
        Gets the fixed part of the plastic region as an array of 16-bit 
        half-words
        """
        raise NotImplementedError

    def get_packed_plastic_region(self, synapse_row, weight_scale,
                                  n_synapse_type_bits):
        """
        Gets the plastic part of the plastic region as an array of 32-bit words
        """
        raise NotImplementedError
    
    def read_packed_plastic_plastic_region(self, synapse_row, data, offset,
                                           length, weight_scale):
        """
        Return a copy of synapse_row which has updated synapse information
        read from length words from data (an array of 32-bit words), 
        starting at offset
        """
        raise NotImplementedError
