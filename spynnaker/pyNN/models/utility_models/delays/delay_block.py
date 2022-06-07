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


class DelayBlock(object):
    """ A block of delays for a vertex.
    """
    __slots__ = [
        "__delay_block"]

    def __init__(self, n_delay_stages, vertex_slice):
        """
        :param int delay_per_stage:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        n_words_per_row = int(math.ceil(vertex_slice.n_atoms / 32.0))
        self.__delay_block = numpy.zeros(
            (n_delay_stages, n_words_per_row), dtype="uint32")

    def add_delay(self, source_id, stage):
        """
        :param int source_id:
        :param int stage:
        """
        word_id, bit_id = divmod(source_id, 32)
        self.__delay_block[int(stage - 1)][word_id] |= (1 << bit_id)

    @property
    def delay_block(self):
        """
        :rtype: ~numpy.ndarray
        """
        return self.__delay_block
