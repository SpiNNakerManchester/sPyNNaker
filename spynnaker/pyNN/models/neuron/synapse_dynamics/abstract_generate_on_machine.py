# Copyright (c) 2017-2023 The University of Manchester
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

from enum import Enum
from spinn_utilities.abstract_base import AbstractBase, abstractproperty,\
    abstractmethod


class MatrixGeneratorID(Enum):
    STATIC_MATRIX = 0
    STDP_MATRIX = 1
    NEUROMODULATION_MATRIX = 2


class AbstractGenerateOnMachine(object, metaclass=AbstractBase):
    """ A synapse dynamics that can be generated on the machine.
    """
    __slots__ = []

    def generate_on_machine(self):
        """ Determines if this instance should be generated on the machine.

        Default implementation returns True

        :rtype: bool
        """
        return True

    @abstractproperty
    def gen_matrix_id(self):
        """ The ID of the on-machine matrix generator.

        :rtype: int
        """

    @abstractmethod
    def gen_matrix_params(
            self, synaptic_matrix_offset, delayed_matrix_offset, app_edge,
            synapse_info, max_row_info, max_pre_atoms_per_core,
            max_post_atoms_per_core):
        """ Any parameters required by the matrix generator.

        :rtype: ~numpy.ndarray(uint32)
        """

    @abstractproperty
    def gen_matrix_params_size_in_bytes(self):
        """ The size of the parameters of the matrix generator in bytes.

        :rtype: int
        """
