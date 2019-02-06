from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from six import add_metaclass


@add_metaclass(AbstractBase)
class AbstractUsesBitFieldFilter(object):

    @abstractmethod
    def bit_field_base_address(self, transceiver, placement):
        """ returns the sdram address for the bit field table data

        :param transceiver: txrx
        :param placement: placement
        :return: the sdram address for the bitfield address
        """

    @abstractmethod
    def synaptic_expander_base_address_and_size(
            self, transceiver, placement):
        """ returns the sdram address for the chip synaptic expander loaded 
        synaptic matrix and the size used by the chip synaptic generator 
        
        :param transceiver: txrx
        :param placement: placement
        :return: tuple containing (the sdram address for the chip synaptic 
        matrix expander address, the size used by the chip synaptic matrix)
        """

