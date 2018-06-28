from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractAdditionalInput(object):
    """ Represents a possible additional independent input for a model.

    .. note::
        Override :py:meth:`set_parameters` only when there is a changing\
        variable to extract.
    """

    __slots__ = ()

    @abstractmethod
    def get_n_parameters(self):
        """ Get the number of parameters for the additional input.

        :return: The number of parameters
        :rtype: int
        """

    @abstractmethod
    def get_parameters(self):
        """ Get the parameters for the additional input.

        :return: An array of parameters
        :rtype: \
            list(:py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`)
        """

    @abstractmethod
    def get_parameter_types(self):
        """ Get the types of the parameters.

        :return: A list of DataType objects, in the order of the parameters
        :rtype: list(:py:class:`data_specification.enums.DataType`)
        """

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the number of CPU cycles executed by\
            ``additional_input_get_input_value_as_current`` and\
            ``additional_input_has_spiked``.
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the SDRAM usage of this additional input.

        :return: The SDRAM usage, in bytes
        :rtype: int
        """
        return self.get_n_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this additional input

        :return: The DTCM usage, in bytes
        :rtype: int
        """
        return self.get_n_parameters() * 4

    def set_parameters(self, parameters, vertex_slice):
        """ Set the parameters for a given subset of neurons.

        :param parameters:\
            the parameter values in a list of numpy arrays, ordered the same\
            as :py:meth:`get_neural_parameters`
        :param vertex_slice: The neurons to which the parameters apply
        """
