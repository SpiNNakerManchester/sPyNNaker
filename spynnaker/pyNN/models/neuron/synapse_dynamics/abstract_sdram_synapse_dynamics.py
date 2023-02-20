# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    def write_parameters(self, spec, region, global_weight_scale,
                         synapse_weight_scales):
        """ Write the synapse parameters to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
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
