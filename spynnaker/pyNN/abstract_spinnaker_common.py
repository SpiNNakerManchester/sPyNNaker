# Copyright (c) 2022 The University of Manchester
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

"""
The code that used to be here has been merged into SpiNNaker

This is now just a depreciation redirect hook
"""

from spynnaker.pyNN.utilities.utility_calls import moved_in_v7
from spynnaker.pyNN.spinnaker import SpiNNaker

moved_in_v7("spynnaker.pyNN.abstract_spinnaker_common",
            "spynnaker.pyNN.spinnaker")


class AbstractSpiNNakerCommon(SpiNNaker):

    def __init__(
            self, graph_label, database_socket_addresses, n_chips_required,
            n_boards_required, timestep, min_delay,
            time_scale_factor=None):
        moved_in_v7("spynnaker.pyNN.abstract_spinnaker_common",
                    "spynnaker.pyNN.spinnaker")
        super(database_socket_addresses,
            time_scale_factor, min_delay, graph_label,
            n_chips_required, n_boards_required, timestep)

    @staticmethod
    def register_binary_search_path(search_path):
        moved_in_v7("spynnaker.pyNN.abstract_spinnaker_common",
                    "spynnaker.pyNN.spinnaker")
        SpiNNaker.register_binary_search_path(search_path)
