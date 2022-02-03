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
            synapse_info, max_row_info, max_atoms_per_core):
        """ Any parameters required by the matrix generator.

        :rtype: ~numpy.ndarray(uint32)
        """

    @abstractproperty
    def gen_matrix_params_size_in_bytes(self):
        """ The size of the parameters of the matrix generator in bytes.

        :rtype: int
        """
