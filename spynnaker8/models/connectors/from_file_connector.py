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
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromFileConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class FromFileConnector(_BaseClass):
    """ Make connections according to a list read from a file.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.FromFileConnector`
        instead.
    """
    # pylint: disable=redefined-builtin
    __slots__ = []

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, callback=None, verbose=False):
        """
        :param str file:
            Either an open file object or the filename of a file containing a
            list of connections, in the format required by
            :py:class:`FromListConnector`.
            Column headers, if included in the file, must be specified using
            a list or tuple, e.g.::

                # columns = ["i", "j", "weight", "delay", "U", "tau_rec"]

            Note that the header requires `#` at the beginning of the line.
        :type file: str or ~io.FileIO
        :param bool distributed:
            Basic pyNN says:

                if this is True, then each node will read connections from a
                file called `filename.x`, where `x` is the MPI rank. This
                speeds up loading connections for distributed simulations.

            .. note::
                Always leave this as False with sPyNNaker, which is not
                MPI-based.
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
        moved_in_v6("spynnaker8.models.connectors",
                    "spynnaker.pyNN.models.neural_projections.connectors")
        _BaseClass.__init__(self, file, distributed, safe, callback, verbose)
