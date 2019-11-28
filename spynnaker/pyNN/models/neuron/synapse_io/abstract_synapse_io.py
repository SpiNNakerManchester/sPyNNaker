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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSynapseIO(object):
    # pylint: disable=too-many-arguments

    __slots__ = ()

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by the synapse representation \
            before extensions are required, or None if any delay is supported

        :param machine_time_step:
        :type machine_time_step: int
        :rtype: int or None
        """

    def get_max_row_info(
            self, synapse_info, post_vertex_slice, n_delay_stages,
            population_table, machine_time_step, in_edge):
        """ Get the information about the maximum lengths of delayed and\
            undelayed rows in bytes (including header), words (without header)\
            and number of synapses

        :param synapse_info:
        :type synapse_info: SynapseInformation
        :param post_vertex_slice:
        :type post_vertex_slice: ~pacman.model.graphs.common.Slice
        :param n_delay_stages:
        :type n_delay_stages: int
        :param population_table:
        :type population_table: AbstractMasterPopTableFactory
        :param machine_time_step:
        :type machine_time_step: int
        :param in_edge:
        :type in_edge: ProjectionApplicationEdge or ProjectionMachineEdge
        :rtype: MaxRowInfo
        """

    @abstractmethod
    def get_synapses(
            self, synapse_info, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales, machine_time_step,
            app_edge, machine_edge):
        """ Get the synapses as an array of words for non-delayed synapses and\
            an array of words for delayed synapses

        :param synapse_info:
        :type synapse_info: SynapseInformation
        :param pre_slices:
        :type pre_slices: list(~pacman.model.graphs.common.Slice)
        :param pre_slice_index:
        :type pre_slice_index: int
        :param post_slices:
        :type post_slices: list(~pacman.model.graphs.common.Slice)
        :param post_slice_index:
        :type post_slice_index: int
        :param pre_vertex_slice:
        :type pre_vertex_slice: ~pacman.model.graphs.common.Slice
        :param post_vertex_slice:
        :type post_vertex_slice: ~pacman.model.graphs.common.Slice
        :param n_delay_stages:
        :type n_delay_stages: int
        :param population_table:
        :type population_table: AbstractMasterPopTableFactory
        :param n_synapse_types:
        :type n_synapse_types: int
        :param weight_scales:
        :type weight_scales: dict(AbstractSynapseType, float)
        :param machine_time_step:
        :type machine_time_step: int
        :param app_edge:
        :type app_edge: ProjectionApplicationEdge
        :param machine_edge:
        :type machine_edge: ProjectionMachineEdge
        :return: (row_data, max_row_length, delayed_row_data, \
            max_delayed_row_length, delayed_source_ids, stages)
        :rtype: \
            tuple(~numpy.ndarray, int, ~numpy.ndarray, int, ~numpy.ndarray, \
            ~numpy.ndarray)
        """

    @abstractmethod
    def read_synapses(
            self, synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            weight_scales, data, delayed_data, n_delay_stages,
            machine_time_step):
        """ Read the synapses for a given projection synapse information\
            object out of the given data

        :param synapse_info:
        :type synapse_info: SynapseInformation
        :param pre_vertex_slice:
        :type pre_vertex_slice: ~pacman.model.graphs.common.Slice
        :param post_vertex_slice:
        :type post_vertex_slice: ~pacman.model.graphs.common.Slice
        :param max_row_length:
        :type max_row_length: int
        :param delayed_max_row_length:
        :type delayed_max_row_length: int
        :param n_synapse_types:
        :type n_synapse_types: int
        :param weight_scales:
        :type weight_scales: dict(AbstractSynapseType, float)
        :param data:
        :type data: bytes or bytearray or memoryview
        :param delayed_data:
        :type delayed_data: bytes or bytearray or memoryview
        :param n_delay_stages:
        :type n_delay_stages: int
        :param machine_time_step:
        :type machine_time_step: int
        :return: array with ``weight`` and ``delay`` columns
        :rtype: ~numpy.ndarray
        """

    @abstractmethod
    def get_block_n_bytes(self, max_row_length, n_rows):
        """ Get the number of bytes in a block given the max row length and\
            number of rows

        :param max_row_length:
        :type max_row_length: int
        :param n_rows:
        :type n_rows: int
        :rtype: int
        """
