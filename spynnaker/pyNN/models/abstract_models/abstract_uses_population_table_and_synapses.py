from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.models.abstract_models import \
    AbstractAcceptsIncomingSynapses


@add_metaclass(AbstractBase)
class AbstractUsesPopulationTableAndSynapses(AbstractAcceptsIncomingSynapses):

    def __init__(self):
        AbstractAcceptsIncomingSynapses.__init__(self)

    @abstractmethod
    def master_pop_table_base_address(self, transceiver, placement):
        """ returns the sdram address for the master pop table data
        """

    @abstractmethod
    def synaptic_matrix_base_address(self, transceiver, placement):
        """ returns the sdram address for the synaptic matrix table data
        """

    @abstractmethod
    def bit_field_base_address(self, transceiver, placement):
        """ returns the sdram address for the synaptic matrix table data
        """

    @abstractmethod
    def synapse_params_base_address(self, transceiver, placement):
        """ returns the sdram address for the synapse params data
        """

    @abstractmethod
    def direct_matrix_base_address(self, transceiver, placement):
        """ returns the sdram address for the direct matrix
        """
