from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseRowIo(object):

    @abstractmethod
    def get_n_words(self, synapse_row, vertex_slice=None):
        """
        Returns the total size of the fixed and plastic regions of the row in
        words
        """

    @abstractmethod
    def get_packed_fixed_fixed_region(self, synapse_row, weight_scale,
                                      n_synapse_type_bits):
        """
        Gets the fixed part of the fixed region as an array of 32-bit words
        """

    @abstractmethod
    def get_packed_fixed_plastic_region(self, synapse_row, weight_scale,
                                        n_synapse_type_bits):
        """
        Gets the fixed part of the plastic region as an array of 16-bit 
        half-words
        """

    @abstractmethod
    def get_packed_plastic_region(self, synapse_row, weight_scale,
                                  n_synapse_type_bits):
        """
        Gets the plastic part of the plastic region as an array of 32-bit words
        """

    @abstractmethod
    def create_row_info_from_elements(self, p_p_entries, f_f_entries,
                                      f_p_entries, bits_reserved_for_type,
                                      weight_scale):
        """
        takes a collection of entries for both fixed fixed, plastic plasitic and
        fixed plastic and returns a synaptic row object for them

        p_p_entries and f_p_entries are ignored due to this model dealing with
        fixed synapses
        """
