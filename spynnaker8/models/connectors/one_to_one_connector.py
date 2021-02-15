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
    OneToOneConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class OneToOneConnector(_BaseClass):
    """
    Where the pre- and postsynaptic populations have the same size, connect\
    cell *i* in the presynaptic population to cell *i* in the postsynaptic\
    population for all *i*.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.OneToOneConnector`
        instead.
    """
    __slots__ = []

    def __init__(self, safe=True, callback=None):
        """
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param callable callback: a function that will be called with the
            fractional progress of the connection routine. An example would
            be `progress_bar.set_level`.

            .. note::
                Not supported by sPyNNaker.
        """
        moved_in_v6("spynnaker8.models.connectors.OneToOneConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".OneToOneConnector")
        _BaseClass.__init__(self, safe=safe, callback=callback)
