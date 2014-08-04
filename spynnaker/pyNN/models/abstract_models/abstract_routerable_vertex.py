from abc import ABCMeta
from six import add_metaclass

import logging
from spynnaker.pyNN.utilities import packet_conversions

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractRouterableVertex(object):

    def __init__(self):
        pass

    def generate_routing_info(self, subedge):
        """
        For the given subedge generate the key and mask for routing.

        :param subedge: The subedge for which to generate the key and mask.
        :returns: A tuple containing the key and mask.
        """
        x, y, p = subedge._pre_subvertex.placement.processor.get_coordinates()

        key = packet_conversions.get_key_from_coords(x, y, p)
        #bodge to deal with external perrifables
        return key, self._app_mask