import numpy

from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_synapse_row_io import AbstractSynapseRowIo
from spynnaker.pyNN.models.neural_properties.\
    synapse_row_info import SynapseRowInfo
from spynnaker.pyNN import exceptions


class PlasticWeightSynapseRowIo(AbstractSynapseRowIo):

    def __init__(self, num_header_words, dendritic_delay_fraction):
        self.num_header_words = num_header_words
        self._dendritic_delay_fraction = dendritic_delay_fraction

    @property
    def dendritic_delay_fraction(self):
        return self._dendritic_delay_fraction

    def get_n_words(self, synapse_row, vertex_slice=None):
        """
        Returns the size of the fixed and plastic regions of the row in words
        """
        # Calculate number of half words that will be required for
        # Both the plastic weights and the fixed control words
        num_half_words = len(synapse_row.target_indices)
        if vertex_slice is not None:
            num_half_words = \
                len(synapse_row.target_indices[0:vertex_slice.n_atoms + 1])
        if (num_half_words % 2) != 0:
            num_half_words += 1

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
        return numpy.zeros(0)

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
        float_delays = numpy.asarray(synapse_row.delays, dtype="float")
        dendritic_delays = numpy.asarray(float_delays
                * float(self.dendritic_delay_fraction), dtype="uint16")
        axonal_delays = numpy.asarray(float_delays
                * (1.0 - float(self.dendritic_delay_fraction)), dtype="uint16")

        ids = synapse_row.target_indices & 0xFF
        shifted_dendritic_delays = (dendritic_delays
                << (8 + n_synapse_type_bits))
        shifted_axonal_delays = axonal_delays << (8 + 4 + n_synapse_type_bits)
        shifted_types = synapse_row.synapse_types << 8

        return numpy.asarray(shifted_axonal_delays | shifted_dendritic_delays
                | shifted_types | ids, dtype='uint16')

    def get_packed_plastic_region(self, synapse_row, weight_scales,
            n_synapse_type_bits):
        """
        Gets the plastic region of the row as an array of 32-bit words
        """
        # Convert per-synapse type weight scales to numpy and
        # Index this to obtain per-synapse weight scales.
        weight_scales_numpy = numpy.array(weight_scales, dtype="float")
        synapse_weight_scales = weight_scales_numpy[synapse_row.synapse_types]

         # Scale weights
        abs_weights = numpy.abs(synapse_row.weights)
        abs_scaled_weights = numpy.rint(abs_weights * synapse_weight_scales).astype("uint16")

        # Check zeros
        zero_float_weights = numpy.where(abs_weights == 0.0)[0]
        zero_scaled_weights = numpy.where(abs_scaled_weights == 0)[0]
        if zero_float_weights.shape != zero_scaled_weights.shape or (zero_float_weights != zero_scaled_weights).any():
            raise Exception("Weight scaling has reduced non-zero weights to zero")

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
                                      weight_scales):
        """
        takes a collection of entries for both fixed fixed, plastic plastic and
        fixed plastic and returns a synaptic row object for them

        f_f_entries are ignored due to this model dealing with plastic synapses
        """

        if len(f_f_entries) > 0:
            raise exceptions.SynapticBlockGenerationException(
                "plastic synapses cannot create row ios from fixed entries.")

        # Calculate masks and convert per-synapse type weight scales to numpy
        synaptic_type_mask = (1 << bits_reserved_for_type) - 1
        delay_mask = (1 << (8 - bits_reserved_for_type)) - 1
        weight_scales_numpy = numpy.array(weight_scales, dtype="float")

        # Extract indices, delays and synapse types from fixed-plastic region
        target_indices = f_p_entries & 0xFF
        delays_in_ticks = (((f_p_entries >> 8) + bits_reserved_for_type)
                           & delay_mask)
        synapse_types = (f_p_entries >> 8) & synaptic_type_mask

        # Index out per-synapse weight scales
        synapse_weight_scales = weight_scales_numpy[synapse_types]

        # Create a half-word view of plastic region without header
        half_words = p_p_entries[self.num_header_words:].view(dtype="uint16")

        # Trim off any extra half-words caused by padding
        half_words = half_words[:len(f_p_entries)]

        # Cast to float and divide by weight scale
        weights = half_words.astype("float") / synapse_weight_scales

        return SynapseRowInfo(target_indices, weights, delays_in_ticks,
                              synapse_types)