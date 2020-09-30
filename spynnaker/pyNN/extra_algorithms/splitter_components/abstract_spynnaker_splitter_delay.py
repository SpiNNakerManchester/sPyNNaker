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
from spinn_utilities.abstract_base import AbstractBase


@add_metaclass(AbstractBase)
class AbstractSpynnakerSplitterDelay(object):

    __slots__ = []

    STR_MESSAGE = "AbstractSpynnakerSplitter governing app vertex {}"

    # max delays supported by a slice split machine vertex
    MAX_SUPPORTED_DELAY_TICS = 16

    def __str__(self):
        return self.STR_MESSAGE.format(self._governed_app_vertex)

    def __repr__(self):
        return self.__str__()

    def max_support_delay(self):
        """ returns the max amount of delay this post vertex can support.
        :return: int saying max delay supported in ticks
        """
        return self.MAX_SUPPORTED_DELAY_TICS
