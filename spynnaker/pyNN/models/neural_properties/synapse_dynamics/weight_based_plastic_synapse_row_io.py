from pacman103.front.common.abstract_synapse_row_io import AbstractSynapseRowIo
from pacman103.front.common.synapse_row_info import SynapseRowInfo
import numpy

class WeightBasedPlasticSynapseRowIo(AbstractSynapseRowIo):
    
    def __init__(self, num_header_words):
        self.num_header_words = num_header_words
    
    def get_n_words(self, synapse_row, lo_atom=None, hi_atom=None):
        """
        Returns the size of the fixed and plastic regions of the row in words 
        """
        # Calculate number of half words that will be required for 
        # Both the plastic weights and the fixed control words
        num_half_words = len(synapse_row.target_indices)
        if lo_atom is not None and hi_atom is not None:
            num_half_words = len(synapse_row.target_indices[
                    lo_atom:hi_atom + 1])
        if (num_half_words % 2) != 0:
            num_half_words = num_half_words + 1
       
        # As fixed-plastic and plastic regions both require this
        # Many half words, this is the number of words!
        num_words = num_half_words + self.num_header_words
        
        return num_words
        
    def get_packed_fixed_fixed_region(self, synapse_row, weight_scale,
            n_synapse_type_bits):
        """
        Gets the fixed part of the fixed region of the row as an array 
        of 32-bit words
        """
        return []
    
    def get_packed_fixed_plastic_region(self, synapse_row, weight_scale,
            n_synapse_type_bits):
        """
        Gets the plastic part of the fixed region of the row as an array 
        of 16-bit words
        """
        
        if (len(synapse_row.target_indices) > 0 
                and numpy.amax(synapse_row.target_indices) > 0xFF):
            raise Exception("One or more target indices are too large")
        
        max_delay = (1 << (8 - n_synapse_type_bits)) - 1
        if len(synapse_row.delays) > 0 and max(synapse_row.delays) > max_delay:
            raise Exception("One or more delays are too large for the row")

        ids = synapse_row.target_indices & 0xFF
        shifted_delays = synapse_row.delays << (8 + n_synapse_type_bits)
        shifted_types = synapse_row.synapse_types << 8

        return numpy.asarray(shifted_delays | shifted_types | ids, 
                dtype='uint16')

    def get_packed_plastic_region(self, synapse_row, weight_scale,
            n_synapse_type_bits):
        """
        Gets the plastic region of the row as an array of 32-bit words
        """
        # Scale absoluate weights and convert to uint16
        abs_scaled_weights = numpy.asarray(
                numpy.abs(synapse_row.weights) * weight_scale, dtype='uint16')

        # As we're packing into uint32s, add extra weight if we have an odd number
        if (len(abs_scaled_weights) % 2) != 0:
            abs_scaled_weights = numpy.asarray(numpy.append(
                    abs_scaled_weights, 0), dtype='uint16')

        # Create view of weights as uint32s
        abs_scaled_weights_view = abs_scaled_weights.view(dtype='uint32')

        # Allocate memory for pre-synaptic event buffer
        pre_synaptic_event_buffer = numpy.zeros(self.num_header_words, 
                dtype='uint32')

        # Combine together into plastic region and return
        plastic_region = numpy.asarray(numpy.append(pre_synaptic_event_buffer, 
                abs_scaled_weights_view), dtype='uint32')
        return plastic_region

    def create_row_info_from_elements(self, p_p_entries, f_f_entries,
                                      f_p_entries, bits_reserved_for_type,
                                      weight_scale):
        """
        takes a collection of entries for both fixed fixed, plastic plasitic and
        fixed plastic and returns a synaptic row object for them

        f_f_entries are ignored due to this model dealing with plastic synapses
        """

        if len(f_f_entries) > 0:
            raise exceptions.SynapticBlockGenerationException(
                "plastic synapses cannot create row ios from fixed entries.")
        target_indices = list()
        weights = list()
        delays_in_ticks = list()
        synapse_types = list()

        #read in each element
        #the fact that the fixed plastic are shorts, means that its numebr is an
        #exact number for entries in the plastic plastic region. Becuase of the
        # pp elements are in shorts but read as ints, the for loop has to
        #  sleectively deicde each section of the int to read given the shorts
        #counter/index ABS and AGR
        for index in range(len(f_p_entries)):
            if index % 2 == 0:
                weights.append((p_p_entries[self.num_header_words + int(index/2)] & 0xFFFF) / weight_scale) # drops delay, type and id
            else:
                weights.append((p_p_entries[self.num_header_words + int(index/2)] >> 16) / weight_scale)

        #read in each element
        for element in f_p_entries:
            target_indices.append(element & 0xFF) # masks by 8 bits
            synaptic_type_mask = (1 << bits_reserved_for_type) - 1
            synapse_types.append((element >> 8) & synaptic_type_mask)
            delay_mask = (1 << (8 - bits_reserved_for_type)) - 1
            delays_in_ticks.append((element >> 8 + bits_reserved_for_type) &
                                   delay_mask)
        return SynapseRowInfo(target_indices, weights, delays_in_ticks,
                              synapse_types)