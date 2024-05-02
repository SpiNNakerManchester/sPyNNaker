# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List, Tuple, Union

from numpy import integer, uint32
from numpy.typing import NDArray

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    ConnectionsArray)

from .abstract_sdram_synapse_dynamics import AbstractSDRAMSynapseDynamics


class AbstractPlasticSynapseDynamics(
        AbstractSDRAMSynapseDynamics, metaclass=AbstractBase):
    """
    Synapses which change over time.
    """
    # pylint: disable=too-many-arguments

    __slots__ = ()

    @abstractmethod
    def get_n_words_for_plastic_connections(self, n_connections: int) -> int:
        """
        Get the number of 32-bit words for `n_connections` in a single row.

        :param int n_connections:
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_plastic_synaptic_data(
            self, connections: ConnectionsArray,
            connection_row_indices: NDArray[integer], n_rows: int,
            n_synapse_types: int,
            max_n_synapses: int, max_atoms_per_core: int) -> Union[
                Tuple[NDArray[uint32], NDArray[uint32],
                      NDArray[uint32], NDArray[uint32]],
                Tuple[List[NDArray[uint32]], List[NDArray[uint32]],
                      NDArray[uint32], NDArray[uint32]]]:
        """
        Get the fixed-plastic data, and plastic-plastic data for each row, and
        lengths for the fixed_plastic and plastic-plastic parts of each row.

        Data is returned as an array made up of an array of 32-bit words for
        each row, for each of the fixed-plastic and plastic-plastic data
        regions.  The row into which connection should go is given by
        `connection_row_indices`, and the total number of rows is given by
        `n_rows`.

        Lengths are returned as an array made up of an integer for each row,
        for each of the fixed-plastic and plastic-plastic regions.

        :param ~numpy.ndarray connections: The connections to get data for
        :param ~numpy.ndarray connection_row_indices:
            The row into which each connection should go
        :param int n_rows: The total number of rows
        :param int n_synapse_types: The number of synapse types
        :param int max_n_synapses: The maximum number of synapses to generate
        :param int max_atoms_per_core: The maximum number of atoms on a core
        :return: (fp_data (2D), pp_data (2D), fp_size (1D), pp_size (1D))
        :rtype:
            tuple(~numpy.ndarray, ~numpy.ndarray, ~numpy.ndarray,
            ~numpy.ndarray)
        """
        raise NotImplementedError

    @abstractmethod
    def get_n_plastic_plastic_words_per_row(
            self, pp_size: NDArray[uint32]) -> NDArray[integer]:
        """
        Get the number of plastic plastic words to be read from each row.

        :param ~numpy.ndarray pp_size:
        """
        raise NotImplementedError

    @abstractmethod
    def get_n_fixed_plastic_words_per_row(
            self, fp_size: NDArray[uint32]) -> NDArray[integer]:
        """
        Get the number of fixed plastic words to be read from each row.

        :param ~numpy.ndarray fp_size:
        """
        raise NotImplementedError

    @abstractmethod
    def get_n_synapses_in_rows(
            self, pp_size: NDArray[uint32],
            fp_size: NDArray[uint32]) -> NDArray[integer]:
        """
        Get the number of synapses in each of the rows with plastic sizes
        `pp_size` and `fp_size`.

        :param ~numpy.ndarray pp_size:
        :param ~numpy.ndarray fp_size:
        """
        raise NotImplementedError

    @abstractmethod
    def read_plastic_synaptic_data(
            self, n_synapse_types: int,
            pp_size: NDArray[uint32], pp_data: List[NDArray[uint32]],
            fp_size: NDArray[uint32], fp_data: List[NDArray[uint32]],
            max_atoms_per_core: int) -> ConnectionsArray:
        """
        Read the connections indicated in the connection indices from the
        data in `pp_data` and `fp_data`.

        :param int n_synapse_types:
        :param ~numpy.ndarray pp_size: 1D
        :param ~numpy.ndarray pp_data: 2D
        :param ~numpy.ndarray fp_size: 1D
        :param ~numpy.ndarray fp_data: 2D
        :param int max_atoms_per_core:
        :return:
            array with columns ``source``, ``target``, ``weight``, ``delay``
        :rtype: ~numpy.ndarray
        """
        raise NotImplementedError
