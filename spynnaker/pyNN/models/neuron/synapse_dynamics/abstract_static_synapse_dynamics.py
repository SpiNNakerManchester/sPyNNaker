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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from .abstract_sdram_synapse_dynamics import AbstractSDRAMSynapseDynamics


class AbstractStaticSynapseDynamics(
        AbstractSDRAMSynapseDynamics, metaclass=AbstractBase):
    """
    Dynamics which don't change over time.
    """
    # pylint: disable=too-many-arguments

    __slots__ = ()

    @abstractmethod
    def get_n_words_for_static_connections(self, n_connections):
        """
        Get the number of 32-bit words for `n_connections` in a single row.

        :param int n_connections:
        :rtype: int
        """

    @abstractmethod
    def get_static_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types, max_n_synapses,
            max_atoms_per_core):
        """
        Get the fixed-fixed data for each row, and lengths for the
        fixed-fixed parts of each row.

        Data is returned as an array made up of an array of 32-bit words for
        each row for the fixed-fixed region. The row into which connection
        should go is given by `connection_row_indices`, and the total number
        of rows is given by `n_rows`.

        Lengths are returned as an array made up of an integer for each row,
        for the fixed-fixed region.

        :param ~numpy.ndarray connections: The connections to get data for
        :param ~numpy.ndarray connection_row_indices:
            The row into which each connection should go
        :param int n_rows: The number of rows to write
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post vertex to generate for
        :param int n_synapse_types: The number of synapse types
        :param int max_n_synapses: The maximum number of synapses to generate
        :param int max_atoms_per_core: The maximum number of atoms on a core
        :return: (ff_data, ff_size)
        :rtype: tuple(list(~numpy.ndarray), ~numpy.ndarray)
        """

    @abstractmethod
    def get_n_static_words_per_row(self, ff_size):
        """
        Get the number of bytes to be read per row for the static data
        given the size that was written to each row.

        :param ~numpy.ndarray ff_size:
        :rtype: ~numpy.ndarray
        """

    @abstractmethod
    def get_n_synapses_in_rows(self, ff_size):
        """
        Get the number of synapses in the rows with sizes `ff_size`.

        :param ~numpy.ndarray ff_size:
        :rtype: ~numpy.ndarray
        """

    @abstractmethod
    def read_static_synaptic_data(
            self, post_vertex_slice, n_synapse_types, ff_size, ff_data,
            max_atoms_per_core):
        """
        Read the connections from the words of data in `ff_data`.

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_synapse_types:
        :param ~numpy.ndarray ff_size:
        :param list(~numpy.ndarray) ff_data:
        :param int max_atoms_per_core:
        :rtype: ~numpy.ndarray
        """
