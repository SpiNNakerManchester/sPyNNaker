from spinn_front_end_common.utilities import exceptions

class SpynnakerException(Exception):
    """Superclass of all exceptions from the pynn module.

    :raise None: does not raise any known exceptions"""
    pass


class MemReadException(SpynnakerException):
    """raised when the pynn front end fails to read a certain memory region

    :raise None: does not raise any known exceptions
    """
    pass

class FilterableException(SpynnakerException):
    """rasied during the pynn's front end pruning of uninportant subedges when\
     a subedge cannot be detemrined if it is prunable or not

    :raise None: does not raise any known exceptions
    """
    pass

class SynapticConfigurationException(exceptions.ConfigurationException):
    """raised when the synaptic manager fails to handle a synaptic dynamic

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticBlockGenerationException(exceptions.ConfigurationException):
    """raised when the synaptic manager fails to generate a synaptic block

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticBlockReadException(exceptions.ConfigurationException):
    """raised when the synaptic manager fails to read a synaptic block or
        convert it into readable values

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticMaxIncomingAtomsSupportException(exceptions.ConfigurationException):
    """raised when a synatpic sublist exceeds the max atoms possible to be
    supported

    :raise None: does not raise any known exceptions
    """
    pass


class DelayExtensionException(exceptions.ConfigurationException):
    """raised when a delay extension vertex is given a subedge that is not from
    a delay DelayAfferentPartitionableEdge

    :raise None: does not raise any known exceptions
    """
    pass