from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractConnector(object):
    """
    Abstract class which connectors extend
    """
    @abstractmethod
    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):
        """
        Generate a list of synapses that can be queried for information and
        connectivity.  Note that this doesn't actually have to store the
        explicit information, as long as it produces the correct information!
        """
