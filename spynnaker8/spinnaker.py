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

from spynnaker.pyNN.spinnaker import SpiNNaker as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v7


class SpiNNaker(_BaseClass):
    """
    Main interface for the sPyNNaker implementation of PyNN 0.8/0.9.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN.SpiNNaker` instead.
    """

    def __init__(
            self, time_scale_factor, min_delay, graph_label,
            n_chips_required=None, n_boards_required=None, timestep=0.1):
        # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        moved_in_v7("spynnaker8.spinnaker",
                    "spynnaker.pyNN.spinnaker")
        super(SpiNNaker, self).__init__(
            time_scale_factor, min_delay,
            n_chips_required, n_boards_required, timestep)
