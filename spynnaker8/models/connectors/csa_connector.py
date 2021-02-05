# Copyright (c) 2017-2021 The University of Manchester
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
import logging
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neural_projections.connectors import (
    CSAConnector as
    _BaseClass)
logger = FormatAdapter(logging.getLogger(__name__))


class CSAConnector(_BaseClass):
    """ A CSA (*Connection Set Algebra*, Djurfeldt 2012) connector.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.CSAConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, cset, safe=True, callback=None, verbose=False):
        """
        :param cset: a connection set description
        :type cset: csa.connset.CSet
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # pylint: disable=too-many-arguments
        super(CSAConnector, self).__init__(
            cset=cset, safe=safe, callback=callback, verbose=verbose)
        logger.warning(
            "please use spynnaker.pyNN.models.neural_projections.connectors."
            "CSAConnector instead")
