# Copyright (c) 2020-2021 The University of Manchester
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
class AbstractSupportsOneToOneSDRAMInput(object):
    """ An interface for a splitter that supports one-to-one input using
        SDRAM.  The splitter is assumed to handle the splitting on any inputs
        that are actually one-to-one, as it will have to create the vertices
    """

    @abstractmethod
    def handles_source_vertex(self, projection):
        """ Determine if the source vertex of the given projection is to be
            handled by the target splitter

        :param Projection projection: The projection to check the source of
        :rtype: bool
        """
