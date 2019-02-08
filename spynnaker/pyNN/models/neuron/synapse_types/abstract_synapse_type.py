from spinn_utilities.abstract_base import abstractmethod
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class AbstractSynapseType(AbstractStandardNeuronComponent):
    """ Represents the synapse types supported.
    """

    __slots__ = ()

    @abstractmethod
    def get_n_synapse_types(self):
        """ Get the number of synapse types supported.

        :return: The number of synapse types supported
        :rtype: int
        """

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the ID of a synapse given the name.

        :return: The ID of the synapse
        :rtype: int
        """

    @abstractmethod
    def get_synapse_targets(self):
        """ Get the target names of the synapse type.

        :return: an array of strings
        :rtype: array(str)
        """
