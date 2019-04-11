from spinn_front_end_common.utilities.exceptions import ConfigurationException


class SpynnakerException(Exception):
    """ Superclass of all exceptions from the PyNN module.
    """


class MemReadException(SpynnakerException):
    """ Raised when the PyNN front end fails to read a certain memory region.
    """


class FilterableException(SpynnakerException):
    """ Raised when it is not possible to determine if an edge should be\
        filtered.
    """


class SynapticConfigurationException(ConfigurationException):
    """ Raised when the synaptic manager fails for some reason.
    """


class SynapticBlockGenerationException(ConfigurationException):
    """ Raised when the synaptic manager fails to generate a synaptic block.
    """


class SynapticBlockReadException(ConfigurationException):
    """ Raised when the synaptic manager fails to read a synaptic block or\
        convert it into readable values.
    """


class SynapticMaxIncomingAtomsSupportException(ConfigurationException):
    """ Raised when a synaptic sublist exceeds the max atoms possible to be\
        supported.
    """


class DelayExtensionException(ConfigurationException):
    """ Raised when a delay extension vertex fails.
    """


class InvalidParameterType(SpynnakerException):
    """ Raised when a parameter is not recognised.
    """


class SynapseRowTooBigException(SpynnakerException):
    """ Raised when a synapse row is bigger than is allowed.PyNN
    """
    def __init__(self, max_size, message):
        super(SynapseRowTooBigException, self).__init__(message)
        self._max_size = max_size

    @property
    def max_size(self):
        """ The maximum size allowed.
        """
        return self._max_size
