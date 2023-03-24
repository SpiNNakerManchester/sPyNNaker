# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The code that used to be here has been merged into SpiNNaker

This is now just a depreciation redirect hook
"""

from spynnaker.pyNN.utilities.utility_calls import (
    moved_in_v7, moved_in_v7_warning)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.spinnaker import SpiNNaker

moved_in_v7("spynnaker.pyNN.abstract_spinnaker_common",
            "spynnaker.pyNN.spinnaker")


class AbstractSpiNNakerCommon(SpiNNaker):

    def __init__(
            self, graph_label, database_socket_addresses, n_chips_required,
            n_boards_required, timestep, min_delay,
            time_scale_factor=None):
        # pylint: disable=super-init-not-called
        moved_in_v7("spynnaker.pyNN.abstract_spinnaker_common",
                    "spynnaker.pyNN.spinnaker")
        super(database_socket_addresses,
              time_scale_factor, min_delay, graph_label,
              n_chips_required, n_boards_required, timestep)

    @staticmethod
    def register_binary_search_path(search_path):
        moved_in_v7_warning("register_binary_search_path is now a View method")
        SpynnakerDataView.register_binary_search_path(search_path)
