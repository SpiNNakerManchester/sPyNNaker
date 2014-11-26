from spynnaker.pyNN.models.neural_properties.\
    synapse_dynamics.abstract_synapse_row_io import AbstractSynapseRowIo
from spynnaker.pyNN.models.neural_properties.\
    synapse_row_info import SynapseRowInfo
import numpy

class SynapseRowIoPlasticWeight(AbstractSynapseRowIo):
    
    def __init__(self, num_header_words, dendritic_delay_fraction):
        self.num_header_words = num_header_words
        self.dendritic_delay_fraction = dendritic_delay_fraction
    
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
    
    def get_packed_fixed_plastic_region(self, synapse_row, weight_scales,
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

        # Use dendritic delay fraction to split delay into components
        float_delays = numpy.asarray(synapse_row.delays, dtype = "float")
        dendritic_delays = numpy.asarray(float_delays * float(self.dendritic_delay_fraction), dtype="uint16")
        axonal_delays = numpy.asarray(float_delays * (1.0 - float(self.dendritic_delay_fraction)), dtype="uint16")
        
        ids = synapse_row.target_indices & 0xFF
        shifted_dendritic_delays = dendritic_delays << (8 + n_synapse_type_bits)
        shifted_axonal_delays = axonal_delays << (8 + 4 + n_synapse_type_bits)        
        shifted_types = synapse_row.synapse_types << 8

        return numpy.asarray(shifted_axonal_delays | shifted_dendritic_delays | shifted_types | ids, 
                dtype='uint16')

    def get_packed_plastic_region(self, synapse_row, weight_scales,
            n_synapse_type_bits):
        """
        Gets the plastic region of the row as an array of 32-bit words
        """
        # Get the correct synapse scale for each element based on their synapse type
        synapse_scales = numpy.array([weight_scales[t] for t in synapse_row.synapse_types], dtype="float")
        
         # Scale weights
        abs_weights = numpy.abs(synapse_row.weights)
        scaled_weights = numpy.rint(abs_weights * synapse_scales).astype("uint16")
        
        # Check zeros
        zero_float_weights = numpy.where(abs_weights == 0.0)[0]
        zero_scaled_weights = numpy.where(scaled_weights == 0)[0]
        if zero_float_weights.shape != zero_scaled_weights.shape or (zero_float_weights != zero_scaled_weights).any():
            raise Exception("Weight scaling has reduced non-zero weights to zero")

        # As we're packing into uint32s, add extra weight if we have an odd number
        if (len(scaled_weights) % 2) != 0:
            scaled_weights = numpy.asarray(numpy.append(
                    scaled_weights, 0), dtype='uint16')

        # Create view of weights as uint32s
        scaled_weights_view = scaled_weights.view(dtype='uint32')

        # Allocate memory for pre-synaptic event buffer
        pre_synaptic_event_buffer = numpy.zeros(self.num_header_words, 
                dtype='uint32')

        # Combine together into plastic region and return
        plastic_region = numpy.asarray(numpy.append(pre_synaptic_event_buffer, 
                scaled_weights_view), dtype='uint32')
        return plastic_region

    def create_row_info_from_elements(self, p_p_entries, f_f_entries,
                                      f_p_entries, bits_reserved_for_type,
                                      weight_scales):
        """
        takes a collection of entries for both fixed fixed, plastic plasitic and
        fixed plastic and returns a synaptic row object for them

        f_f_entries are ignored due to this model dealing with plastic synapses
        """
        # Generate masks
        synaptic_type_mask = (1 << bits_reserved_for_type) - 1
        delay_mask = (1 << (8 - bits_reserved_for_type)) - 1
        
        if len(f_f_entries) > 0:
            raise exceptions.SynapticBlockGenerationException(
                "plastic synapses cannot create row ios from fixed entries.")
        target_indices = list()
        weights = list()
        delays_in_ticks = list()
        synapse_types = list()

        # Read fixed plastic region
        for element in f_p_entries:
            target_indices.append(element & 0xFF) # masks by 8 bits
            synapse_types.append((element >> 8) & synaptic_type_mask)
            delays_in_ticks.append((element >> 8 + bits_reserved_for_type) &
                                   delay_mask)
            
        #read in each element
        #the fact that the fixed plastic are shorts, means that its numebr is an
        #exact number for entries in the plastic plastic region. Becuase of the
        # pp elements are in shorts but read as ints, the for loop has to
        #  sleectively deicde each section of the int to read given the shorts
        #counter/index ABS and AGR
        #read in each element
        for index, synapse_type in enumerate(synapse_types):
            weight_scale = float(weight_scales[synapse_type])
            
            if index % 2 == 0:
                weights.append((p_p_entries[self.num_header_words + int(index/2)] & 0xFFFF) / weight_scale) # drops delay, type and id
            else:
                weights.append((p_p_entries[self.num_header_words + int(index/2)] >> 16) / weight_scale)

        
        return SynapseRowInfo(target_indices, weights, delays_in_ticks,
                              synapse_types)