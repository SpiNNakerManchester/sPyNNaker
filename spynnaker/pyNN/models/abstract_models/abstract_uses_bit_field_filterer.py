from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from six import add_metaclass


@add_metaclass(AbstractBase)
class AbstractUsesBitFieldFilter(object):

    @abstractmethod
    def bit_field_base_address(self, transceiver, placement):
        """ returns the sdram address for the synaptic matrix table data

        :param transceiver: txrx
        :param placement: placement
        :return: the sdram address for the bitfield address
        """
