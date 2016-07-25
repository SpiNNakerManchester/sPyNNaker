from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from spynnaker.pyNN.models.common.bag_of_neuron_settable import \
    BagOfNeuronSettable


@add_metaclass(ABCMeta)
class AbstractAdditionalInput(BagOfNeuronSettable):
    """ Represents a possible additional independent input for a model
    """

    def __init__(self):
        BagOfNeuronSettable.__init__(self)

    @abstractmethod
    def get_n_parameters(self):
        """ Get the number of parameters for the additional input

        :return: The number of parameters
        :rtype: int
        """

    @abstractmethod
    def get_parameters(self, atom_id):
        """ Get the parameters for the additional input

        :return: An array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the number of CPU cycles executed by\
            additional_input_get_input_value_as_current and\
            additional_input_has_spiked
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the SDRAM usage of this additional input in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return self.get_n_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this additional input in bytes

        :return: The DTCM usage
        :rtype: int
        """
        return self.get_n_parameters() * 4
