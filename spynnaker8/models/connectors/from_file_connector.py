# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromFileConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class FromFileConnector(_BaseClass):
    """
    Make connections according to a list read from a file.

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
