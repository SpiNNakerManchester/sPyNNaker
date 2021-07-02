# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)


class Is2DSource(object, metaclass=AbstractBase):
    """ Indicates that the spikes sent by this source are arranged in 2D, and
        that the keys sent will reflect this 2D structure, formatted as:
        | K | P | Y | X |
        K is the key of the sender
        P is the "polarity" of the sender (optional: for DVS devices)
        Y is the y-coordinate of the sender
        X is the x-coordinate of the sender
        The X and Y will be in fields appropriate to their size.

        Note: this has abstract properties to allow mixing with other things.
    """

    __slots__ = []

    @abstractproperty
    def is_source_2d(self):
        """ Although the source supports 2D, this indicates whether it is
            actually using 2D coordinates now.

        :rtype: bool
        """

    @abstractproperty
    def source_dims(self):
        """ Indicates the width and height of the source

        :return: width, height
        :rtype: int, int
        """

    @abstractmethod
    def source_slices(self, machine_vertex):
        """ The slices of the source sent by this vertex in each dimension,
            as well as a mask in case the coordinates are non-continuous

        :param machine_vertex: The machine vertex to get the slice of

        :return: slice of x, mask of x, slice of y, mask of y
        :rtype: (~pacman.model.graphs.common.Slice, int,
                 ~pacman.model.graphs.common.Slice, int)
        """
