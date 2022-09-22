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

from spinn_utilities.abstract_base import AbstractBase


class AbstractSpynnakerSplitterDelay(object, metaclass=AbstractBase):
    """
    Defines that a splitter is able to handle delays in some way.

    Ideally the splitter and therefore the vertices it creates are able to
    handle some delay themselves and if more is needed have the ability to
    accept spikes from a :py:class:`DelayExtensionMachineVertex`
    """

    __slots__ = []

    # max delays supported by a slice split machine vertex
    MAX_SUPPORTED_DELAY_TICS = 64  # can this be 16?

    def max_support_delay(self):
        """
        returns the max amount of delay this post vertex can support.

        :return: max delay supported in ticks
        :rtype: int
        """
        return self.MAX_SUPPORTED_DELAY_TICS

    def accepts_edges_from_delay_vertex(self):
        """
        Confirms that the splitter's vertices can handle spikes coming from a \
        :py:class:`DelayExtensionMachineVertex`.

        If this method returns False and the users ask for a delay larger than
        that allowed by :py:meth:`max_support_delay`, an exception will be
        raised saying a different splitter is required.

        :rtype: bool
        """
        return True
