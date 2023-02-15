# Copyright (c) 2017 The University of Manchester
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
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.models.common import PopulationApplicationVertex


class ExternalCochleaDevice(
        ApplicationSpiNNakerLinkVertex, PopulationApplicationVertex):
    __slots__ = []

    def __init__(
            self, n_neurons, spinnaker_link, label=None, board_address=None):
        """
        :param int n_neurons: Number of neurons
        :param int spinnaker_link:
            The SpiNNaker link to which the cochlea is connected
        :param str label:
        :param str board_address:
        """
        super().__init__(
            n_atoms=n_neurons, spinnaker_link_id=spinnaker_link,
            label=label, board_address=board_address)
