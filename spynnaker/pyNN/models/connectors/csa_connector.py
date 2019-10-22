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
    CSAConnector as
    CommonCSAConnector)


class CSAConnector(CommonCSAConnector):
    """
    Create an CSA (Connection Set Algebra, Djurfeldt 2012) connector.

    :param cset: a connection set description
    :type cset: string
    """
    __slots__ = []

    def __init__(
            self, cset, safe=True, callback=None, verbose=False):
        # pylint: disable=too-many-arguments
        super(CSAConnector, self).__init__(
            cset=cset,
            safe=safe, callback=callback, verbose=verbose)
