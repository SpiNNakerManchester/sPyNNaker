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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractExpanable(object):
    """ Indicates an object that can expanded on machine
    """
    __slots__ = ()

    @abstractmethod
    def gen_on_machine(self, vertex_slice):
        """
        Dettermines if this slice can generate on machine
        :param vertex_slice:\
            The slice of atoms that the machine vertex will cover
        :type vertex_slice: ~pacman.model.graphs.common.Slice
        :return: True if vertex should be expanded on machone
        :rtype: bool
        """
