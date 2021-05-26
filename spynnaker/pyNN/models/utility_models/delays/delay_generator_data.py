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

import numpy
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION, BYTES_PER_WORD)
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step)


class DelayGeneratorData(object):
    """ Data for each connection of the delay generator
    """
    __slots__ = (
        "__max_delayed_row_n_synapses",
        "__max_row_n_synapses",
        "__max_stage",
        "__delay_per_stage",
        "__post_slices",
        "__post_vertex_slice",
        "__pre_slices",
        "__pre_vertex_slice",
        "__synapse_information")

    BASE_SIZE = 9 * BYTES_PER_WORD

    def __init__(
            self, max_row_n_synapses, max_delayed_row_n_synapses,
            pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_information, max_stage, delay_per_stage):
        """
        :param int max_row_n_synapses:
        :param int max_delayed_row_n_synapses:
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param ~pacman.model.graphs.common.Slicepre_vertex_slice:
        :param ~pacman.model.graphs.common.Slicepost_vertex_slice:
        :param SynapseInformation synapse_information:
        :param int max_stage:
        :param int delay_per_stage:
        """
        self.__max_row_n_synapses = max_row_n_synapses
        self.__max_delayed_row_n_synapses = max_delayed_row_n_synapses
        self.__pre_slices = pre_slices
        self.__post_slices = post_slices
        self.__pre_vertex_slice = pre_vertex_slice
        self.__post_vertex_slice = post_vertex_slice
        self.__synapse_information = synapse_information
        self.__max_stage = max_stage
        self.__delay_per_stage = delay_per_stage

    @property
    def size(self):
        """ The size of the generated data in bytes

        :rtype: int
        """
        connector = self.__synapse_information.connector

        return (
            self.BASE_SIZE + connector.gen_connector_params_size_in_bytes +
            connector.gen_delay_params_size_in_bytes(
                self.__synapse_information.delays))

    @property
    def gen_data(self):
        """ Get the data to be written for this connection

        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        connector = self.__synapse_information.connector
        items = list()
        items.append(numpy.array([
            self.__max_row_n_synapses,
            self.__max_delayed_row_n_synapses,
            self.__post_vertex_slice.lo_atom,
            self.__post_vertex_slice.n_atoms,
            self.__max_stage,
            self.__delay_per_stage,
            DataType.S1615.encode_as_int(
                MICRO_TO_MILLISECOND_CONVERSION /
                machine_time_step()),
            connector.gen_connector_id,
            connector.gen_delays_id(self.__synapse_information.delays)],
            dtype="uint32"))
        items.append(connector.gen_connector_params(
            self.__pre_slices, self.__post_slices, self.__pre_vertex_slice,
            self.__post_vertex_slice, self.__synapse_information.synapse_type,
            self.__synapse_information))
        items.append(connector.gen_delay_params(
            self.__synapse_information.delays, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        return numpy.concatenate(items)
