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

from spynnaker.pyNN.models.neural_projections.connectors import (
    ArrayConnector as CommonArrayConnector)


class ArrayConnector(CommonArrayConnector):
    """ Make connections using an array of integers based on the IDs\
        of the neurons in the pre- and post-populations.
    """
    __slots__ = []

    def __init__(
            self, array, safe=True, callback=None, verbose=False):
        """
        :param array: an array of integers
        :type array: ~numpy.ndarray(2, ~numpy.uint8)
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        # pylint: disable=too-many-arguments
        super(ArrayConnector, self).__init__(
            array=array,
            safe=safe, callback=callback, verbose=verbose)
