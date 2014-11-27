import numpy
import math

from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_synapse_row_io import AbstractSynapseRowIo
from spynnaker.pyNN.models.neural_properties.\
    synapse_row_info import SynapseRowInfo
from spynnaker.pyNN import exceptions


class PlasticWeightControlSynapseRowIo(AbstractSynapseRowIo):

    def __init__(self, num_header_words, dendritic_delay_fraction, signed):
        self._num_header_words = num_header_words
        self._dendritic_delay_fraction = dendritic_delay_fraction
        self._signed = signed

    @property
    def dendritic_delay_fraction(self):
        return self._dendritic_delay_fraction

    def get_n_words(self, synapse_row, vertex_slice=None):
        """
        Returns the size of the fixed and plastic regions of the row in words
        """
        # Calculate number of half words that will be required for
        # Both the plastic weights and the fixed control words
        num_synapses = len(synapse_row.target_indices)
        if vertex_slice is not None:
            num_synapses = \
                len(synapse_row.target_indices[0:vertex_slice.n_atoms + 1])

        # If there are an odd number of synapses, round up number
        # Of control half-words so they will be word-aligned
        num_fixed_plastic_words = math.ceil(num_synapses / 2)

        # As fixed-plastic and plastic regions both require this
        # Many half words, this is the number of words!
        num_words = (num_synapses + num_fixed_plastic_words
                + self._num_header_words)

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

    def get_packed_plastic_region(self, synapse_row, weight_scale,
                                  n_synapse_type_bits):
        """
        Gets the plastic region of the row as an array of 32-bit words
        """
        # Scale absoluate weights and convert to uint16
        half_word_datatype = None
        scaled_weights = None
        if self.signed:
            scaled_weights = numpy.asarray(synapse_row.weights * weight_scale,
                    dtype="int16")
            half_word_datatype = "int16"
        else:
            scaled_weights = numpy.asarray(numpy.abs(synapse_row.weights)
                    * weight_scale, dtype="uint16")
            half_word_datatype = "uint16"

        # Interleave these with zeros and get uint32 view
        padded_weights = numpy.zeros(len(scaled_weights) * 2,
                dtype=half_word_datatype)
        padded_weights[0::2] = scaled_weights
        padded_weights_view = padded_weights.view(dtype="uint32")

        # Allocate memory for pre-synaptic event buffer
        pre_synaptic_event_buffer = numpy.zeros(self.num_header_words,
                                                dtype='uint32')

        # Combine together into plastic region and return
        plastic_region = numpy.asarray(numpy.append(pre_synaptic_event_buffer,
            padded_weights_view), dtype='uint32')
        return plastic_region

    def create_row_info_from_elements(self, p_p_entries, f_f_entries,
                                      f_p_entries, bits_reserved_for_type,
                                      weight_scale):
        """
        takes a collection of entries for both fixed fixed, plastic plastic
        and fixed plastic and returns a synaptic row object for them

        f_f_entries are ignored due to this model dealing with plastic synapses
        """

        if len(f_f_entries) > 0:
            raise exceptions.SynapticBlockGenerationException(
                "plastic synapses cannot create row ios from fixed entries.")

        synaptic_type_mask = (1 << bits_reserved_for_type) - 1
        delay_mask = (1 << (8 - bits_reserved_for_type)) - 1

        target_indices = f_p_entries & 0xFF
        delays_in_ticks = (((f_p_entries >> 8) + bits_reserved_for_type)
                           & delay_mask)
        synapse_types = (f_p_entries >> 8) & synaptic_type_mask

        # Convert plastic region entries to numpy array
        # **TODO** why aren't they read in as this
        numpy_p_p = numpy.asarray(p_p_entries, dtype="uint32")

        # Get half word view of plastic region with correct signedness
        half_word_datatype = "int16" if self.signed else "uint16"
        half_words = numpy_p_p[self.num_header_words:].view(
                dtype=half_word_datatype)

        # Slice out weight half words, convert to float and divide by weight
        # scale
        weights = list(numpy.divide(numpy.asarray(half_words[0::2],
                dtype="float"), weight_scale))

        return SynapseRowInfo(target_indices, weights, delays_in_ticks,
                              synapse_types)
