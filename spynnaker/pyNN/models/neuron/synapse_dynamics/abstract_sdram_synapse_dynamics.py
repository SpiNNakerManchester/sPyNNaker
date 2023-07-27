# Copyright (c) 2021 The University of Manchester
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

import math
import numpy
from numpy import floating, integer, uint32
from numpy.typing import NDArray
from typing import List, Optional
from spinn_utilities.abstract_base import abstractmethod
from spinn_front_end_common.interface.ds import DataSpecificationBase
from .abstract_synapse_dynamics import AbstractSynapseDynamics
from .abstract_has_parameter_names import AbstractHasParameterNames


class AbstractSDRAMSynapseDynamics(
        AbstractSynapseDynamics, AbstractHasParameterNames):
    """
    How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ()

    @abstractmethod
    def is_same_as(self, synapse_dynamics: AbstractSynapseDynamics) -> bool:
        """
        Determines if this synapse dynamics is the same as another.

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: bool
        """
        raise NotImplementedError

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(
            self, n_neurons: int, n_synapse_types: int) -> int:
        """
        Get the SDRAM usage of the synapse dynamics parameters in bytes.

        :param int n_neurons:
        :param int n_synapse_types:
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def write_parameters(
            self, spec: DataSpecificationBase, region: int,
            global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]):
        """
        Write the synapse parameters to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
        """
        raise NotImplementedError

    @abstractmethod
    def get_max_synapses(self, n_words: int) -> int:
        """
        Get the maximum number of synapses that can be held in the given
        number of words.

        :param int n_words: The number of words the synapses must fit in
        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def pad_to_length(self) -> Optional[int]:
        """
        The amount each row should pad to, or `None` if not specified.
        """
        raise NotImplementedError

    def convert_per_connection_data_to_rows(
            self, connection_row_indices: NDArray[integer], n_rows: int,
            data: NDArray, max_n_synapses: int) -> List[NDArray]:
        """
        Converts per-connection data generated from connections into
        row-based data to be returned from get_synaptic_data.

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

    def get_n_items(
            self, rows: List[NDArray], item_size: int) -> NDArray[uint32]:
        """
        Get the number of items in each row as 4-byte values, given the
        item size.

        :param ~numpy.ndarray rows:
        :param int item_size:
        :rtype: ~numpy.ndarray
        """
        return numpy.array([
            int(math.ceil(float(row.size) / float(item_size)))
            for row in rows], dtype=uint32).reshape((-1, 1))

    def get_words(self, rows: List[NDArray]) -> List[NDArray[uint32]]:
        """
        Convert the row data to words.

        :param ~numpy.ndarray rows:
        :rtype: ~numpy.ndarray
        """
        words = [numpy.pad(
            row, (0, (4 - (row.size % 4)) & 0x3), mode="constant",
            constant_values=0).view(uint32) for row in rows]
        return words
