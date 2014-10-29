

class SpynnakerException(Exception):
    """Superclass of all exceptions from the pynn module.

    :raise None: does not raise any known exceptions"""
    pass


class ConfigurationException(SpynnakerException):
    """raised when the pynn front end determines a input param is invalid

    :raise None: does not raise any known exceptions"""
    pass


class MemReadException(SpynnakerException):
    """raised when the pynn front end fails to read a certain memory region

    :raise None: does not raise any known exceptions
    """
    pass


class RallocException(SpynnakerException):
    """rasied when the pynn front end detects that a routing error has occured
    (during multicast soruce)

    :raise None: does not raise any known exceptions
    """
    pass


class FilterableException(SpynnakerException):
    """rasied during the pynn's front end pruning of uninportant subedges when\
     a subedge cannot be detemrined if it is prunable or not

    :raise None: does not raise any known exceptions
    """
    pass

class SynapticConfigurationException(ConfigurationException):
    """raised when the synaptic manager fails to handle a synaptic dynamic

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticBlockGenerationException(ConfigurationException):
    """raised when the synaptic manager fails to generate a synaptic block

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticBlockReadException(ConfigurationException):
    """raised when the synaptic manager fails to read a synaptic block or
        convert it into readable values

    :raise None: does not raise any known exceptions
    """
    pass


class SynapticMaxIncomingAtomsSupportException(ConfigurationException):
    """raised when a synatpic sublist exceeds the max atoms possible to be
    supported

    :raise None: does not raise any known exceptions
    """
    pass


class DelayExtensionException(ConfigurationException):
    """raised when a delay extension vertex is given a subedge that is not from
    a delay DelayAfferentPartitionableEdge

    :raise None: does not raise any known exceptions
    """
    pass

class ExecutableNotFoundException(SpynnakerException):
    """ raised when a suitable executable cannot be found
    to load onto SpiNNaker for a particular vertex


    :raise None: does not raise any known exceptions
    """
    pass
    
class ExecutableFailedToStartException(SpynnakerException):
    """ raised when the messgaes from the trnasicever state that some or all the
    application images pushed to the board have failed to start when asked


    :raise None: does not raise any known exceptions
    """
    pass


class ExecutableFailedToStopException(SpynnakerException):
    """ raised when the messgaes from the trnasicever state that some or all the
    application images pushed to the board have failed to stop when expected


    :raise None: does not raise any known exceptions
    """
    pass