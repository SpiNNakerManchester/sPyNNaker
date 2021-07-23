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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class HasShapeKeyFields(object, metaclass=AbstractBase):
    """ Indicates a source that has keys in fields for each dimension of the
        source
    """

    __slots__ = []

    @abstractmethod
    def get_shape_key_fields(self, machine_vertex):
        """ Get the fields to be used for each dimension in the shape of the
            given source machine vertex, as a list of mask-and-shift values
            in the order of the fields

        :rtype: list(tuple(int, int))
        """
