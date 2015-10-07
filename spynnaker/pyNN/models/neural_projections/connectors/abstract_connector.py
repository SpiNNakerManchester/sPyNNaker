from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from pyNN.random import RandomDistribution


@add_metaclass(ABCMeta)
class AbstractConnector(object):
    """ Abstract class which PyNN Connectors extend
    """

    @staticmethod
    def _get_maximum_delay(delays):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays
        """
        if isinstance(delays, RandomDistribution):
            if delays.boundaries is None:
                return None
        elif not hasattr(delays, '__iter__'):
            return delays
        else:
            return max(delays)

    @abstractmethod
    def get_maximum_delay(self):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded
        """

    @abstractmethod
    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):
        """ Generate a list of synapses that can be queried for information\
            and connectivity.  Note that this doesn't actually have to store\
            the explicit information, as long as it produces the correct\
            information!
        """
