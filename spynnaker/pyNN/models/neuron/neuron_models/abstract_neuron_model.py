from spinn_utilities.overrides import overrides
import numpy
from spynnaker.pyNN.models.neuron.implementations.struct import Struct
from spynnaker.pyNN.models.neuron.implementations \
    import AbstractStandardNeuronComponent


class AbstractNeuronModel(AbstractStandardNeuronComponent):
    """ Represents a neuron model
    """

    __slots__ = ("_global_struct")

    def __init__(self, data_types, global_data_types=None):
        """

        :param data_types:\
            A list of data types in the neuron structure, in the order that\
            they appear
        :param global_data_types:\
            A list of data types in the neuron global structure, in the order\
            that they appear

        """
        super(AbstractNeuronModel, self).__init__(data_types)
        if global_data_types is None:
            global_data_types = []
        self._global_struct = Struct(global_data_types)

    @property
    def global_struct(self):
        """ Get the global parameters structure
        """
        return self._global_struct

    @overrides(AbstractStandardNeuronComponent.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        usage = super(AbstractNeuronModel, self).get_dtcm_usage_in_bytes(
            n_neurons)
        return usage + (self.global_struct.get_size_in_whole_words() * 4)

    @overrides(AbstractStandardNeuronComponent.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        usage = super(AbstractNeuronModel, self).get_sdram_usage_in_bytes(
            n_neurons)
        return usage + (self.global_struct.get_size_in_whole_words() * 4)

    def get_global_values(self):
        """ Get the global values to be written to the machine for this model

        :return: A list with the same length as self.global_struct.field_types
        :rtype: A list of single values
        """
        return numpy.zeros(0, dtype="uint32")

    @overrides(AbstractStandardNeuronComponent.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):
        super_data = super(AbstractNeuronModel, self).get_data(
            parameters, state_variables, vertex_slice)
        values = self.get_global_values()
        global_data = self.global_struct.get_data(values)
        return numpy.concatenate([global_data, super_data])

    @overrides(AbstractStandardNeuronComponent.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Assume that the global data doesn't change
        offset += (self.global_struct.get_size_in_whole_words() * 4)
        return super(AbstractNeuronModel, self).read_data(
            self, data, offset, vertex_slice, parameters, state_variables)
