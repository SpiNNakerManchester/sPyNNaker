from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class HasSynapses(object):

    @abstractmethod
    def get_connections_from_machine(
            self, transceiver, placement, app_edge, synapse_info):
        """ Get the connections from the machine for this vertex.

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the connection data
        :param ~pacman.model.placement.Placement placements:
            Where the connection data is on the machine
        :param ProjectionApplicationEdge app_edge:
            The edge for which the data is being read
        :param SynapseInformation synapse_info:
            The specific projection within the edge
        """

    @abstractmethod
    def clear_connection_cache(self):
        """ Flush the cache of connection information; needed for a second run
        """
