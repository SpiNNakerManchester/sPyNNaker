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

from spynnaker.pyNN.spinnaker import SpiNNaker as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v7


class SpiNNaker(_BaseClass):
    """ Main interface for the sPyNNaker implementation of PyNN 0.8/0.9

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN.SpiNNaker` instead.
    """

    def __init__(
            self, time_scale_factor, min_delay, graph_label,
            n_chips_required=None, n_boards_required=None, timestep=0.1):
        # pylint: disable=too-many-arguments, too-many-locals
        moved_in_v7("spynnaker8.spinnaker",
                    "spynnaker.pyNN.spinnaker")
        super(SpiNNaker, self).__init__(
            time_scale_factor, min_delay, graph_label,
            n_chips_required, n_boards_required, timestep)
