

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