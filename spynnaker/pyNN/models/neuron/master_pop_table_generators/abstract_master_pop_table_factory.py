# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod

logger = logging.getLogger(__name__)


@add_metaclass(AbstractBase)
class AbstractMasterPopTableFactory(object):
    # pylint: disable=too-many-arguments

    __slots__ = ()

    @abstractmethod
    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        """
        :param incoming_key: \
            the source key which the synaptic matrix needs to be mapped to
        :param master_pop_base_mem_address: the base address of the master pop
        :param txrx: the transceiver object
        :param chip_y: the y coordinate of the chip of this master pop
        :param chip_x: the x coordinate of the chip of this master pop
        :type incoming_key: int
        :type master_pop_base_mem_address: int
        :type chip_y: int
        :type chip_x: int
        :type txrx: :py:class:`spinnman.transceiver.Transceiver`
        :return: a synaptic matrix memory position.
        """

    @abstractmethod
    def update_master_population_table(
            self, spec, block_start_addr, row_length, key_and_mask,
            master_pop_table_region, is_single=False):
        """ Update a data specification with a master pop entry in some form

        :param spec: the data specification to write the master pop entry to
        :param block_start_addr: the start address of the row in the region
        :param row_length: the row length of this entry
        :param key_and_mask: a key_and_mask object used as part of describing\
            an edge that will require being received to be stored in the\
            master pop table; the whole edge will become multiple calls to\
            this function
        :type key_and_mask: \
            :py:class:`pacman.model.routing_info.BaseKeyAndMask`
        :param master_pop_table_region: \
            The region to which the master pop table is being stored
        :param is_single: True if this is a single synapse, False otherwise
        """

    @abstractmethod
    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ Complete the master pop table in the data specification.

        :param spec: the data specification to write the master pop entry to
        :param master_pop_table_region: \
            the region to which the master pop table is being stored
        """

    @abstractmethod
    def get_edge_constraints(self):
        """ Gets the constraints for this table on edges coming in to a vertex.

        :return: a list of constraints
        :rtype: list(:py:class:`pacman.model.constraints.AbstractConstraint`)
        """

    @abstractmethod
    def get_master_population_table_size(self, vertex_slice, in_edges):
        """ Get the size of the master population table in SDRAM
        """
