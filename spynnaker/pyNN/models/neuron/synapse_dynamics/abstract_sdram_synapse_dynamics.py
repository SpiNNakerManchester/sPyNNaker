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

import math
import numpy
from spinn_utilities.abstract_base import abstractmethod, abstractproperty
from .abstract_synapse_dynamics import AbstractSynapseDynamics


class AbstractSDRAMSynapseDynamics(AbstractSynapseDynamics):
    """ How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ()

    #: Type model of the basic configuration data of a connector
    NUMPY_CONNECTORS_DTYPE = [("source", "uint32"), ("target", "uint32"),
                              ("weight", "float64"), ("delay", "float64")]

    @abstractmethod
    def is_same_as(self, synapse_dynamics):
        """ Determines if this synapse dynamics is the same as another

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: bool
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        """ Get the SDRAM usage of the synapse dynamics parameters in bytes

        :param int n_neurons:
        :param int n_synapse_types:
        :rtype: int
        """

    @abstractmethod
    def write_parameters(self, spec, region, weight_scales):
        """ Write the synapse parameters to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
        :param int region: region ID
        :param list(float) weight_scales:
        """

    @abstractmethod
    def get_parameter_names(self):
        """ Get the parameter names available from the synapse \
            dynamics components

        :rtype: iterable(str)
        """

    @abstractmethod
    def get_max_synapses(self, n_words):
        """ Get the maximum number of synapses that can be held in the given\
            number of words

        :param int n_words: The number of words the synapses must fit in
        :rtype: int
        """

    @abstractproperty
    def pad_to_length(self):
        """ The amount each row should pad to, or None if not specified
        """

    def convert_per_connection_data_to_rows(
            self, connection_row_indices, n_rows, data, max_n_synapses):
        """ Converts per-connection data generated from connections into\
            row-based data to be returned from get_synaptic_data

        :param ~numpy.ndarray connection_row_indices:
            The index of the row that each item should go into
        :param int n_rows:
            The number of rows
        :param ~numpy.ndarray data:
            The non-row-based data
        :param int max_n_synapses:
            The maximum number of synapses to generate in each row
        :rtype: list(~numpy.ndarray)
        """
        return [
            data[connection_row_indices == i][:max_n_synapses].reshape(-1)
            for i in range(n_rows)]

    def get_n_items(self, rows, item_size):
        """ Get the number of items in each row as 4-byte values, given the\
            item size

        :param ~numpy.ndarray rows:
        :param int item_size:
        :rtype: ~numpy.ndarray
        """
        return numpy.array([
            int(math.ceil(float(row.size) / float(item_size)))
            for row in rows], dtype="uint32").reshape((-1, 1))

    def get_words(self, rows):
        """ Convert the row data to words

        :param ~numpy.ndarray rows:
        :rtype: ~numpy.ndarray
        """
        words = [numpy.pad(
            row, (0, (4 - (row.size % 4)) & 0x3), mode="constant",
            constant_values=0).view("uint32") for row in rows]
        return words
