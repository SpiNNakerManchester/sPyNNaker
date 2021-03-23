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

from collections import defaultdict


class ExtractedData(object):
    """ Data holder for all synaptic data being extracted in parallel.
    """
    # @Chimp: play here to hearts content.

    __slots__ = ["__data"]

    def __init__(self):
        self.__data = defaultdict(dict)

    def get(self, projection, attribute):
        """ Allow getting data from a given projection and attribute

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            the projection data was extracted from
        :param attribute: the attribute to retrieve
        :type attribute: list(int) or tuple(int) or None
        :return: the attribute data in a connection holder
        :rtype: ConnectionHolder
        """
        if projection in self.__data:
            if attribute in self.__data[projection]:
                return self.__data[projection][attribute]
        return None

    def set(self, projection, attribute, data):
        """ Allow the addition of data from a projection and attribute.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            the projection data was extracted from
        :param attribute: the attribute to store
        :type attribute: list(int) or tuple(int) or None
        :param ConnectionHolder data:
            attribute data in a connection holder
        :rtype: None
        """
        self.__data[projection][attribute] = data
