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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD


class AbstractCachesSlices(object):
    """ Connector that caches slices
    """

    __slots__ = ()

    def cache_slices(self, pre_slice, post_slice):
        """ Caches a pre and post slice.

        The method allows the connector to build up a set of all the
            pre and post slices that it needs to handle

        Note: the same pre or post slice may be used in multiple calls
        :param Slice pre_slice: Slice of the pre machine vertex
        :param Slice post_slice: Slice of the application machine vertex
        """
