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

from spinn_front_end_common.utility_models import MultiCastCommand
from spinn_front_end_common.utilities.connections import LiveEventConnection


class EthernetControlConnection(LiveEventConnection):
    """
    A connection that can translate Ethernet control messages received
    from a Population.
    """
    __slots__ = ["__translators"]

    def __init__(
            self, translator, label, live_packet_gather_label, local_host=None,
            local_port=None):
        """
        :param AbstractEthernetTranslator translator:
            The translator of multicast to control commands
        :param str label: The label of the vertex to attach the translator to
        :param str live_packet_gather_label: The label of the LPG vertex that
            this control connection will listen to.
        :param str local_host: The optional host to listen on
        :param int local_port: The optional port to listen on
        """
        super().__init__(
            live_packet_gather_label, receive_labels=[label],
            local_host=local_host, local_port=local_port)
        self.__translators = dict()
        self.__translators[label] = translator
        self.add_receive_live_callback(
            label, self._translate, translate_key=False)

    def add_translator(self, label, translator):
        """
        Add another translator that routes via the LPG.

        :param str label: The label of the vertex to attach the translator to
        :param AbstractEthernetTranslator translator:
            The translator of multicast to control commands
        """
        super().add_receive_label(label)
        self.__translators[label] = translator
        self.add_receive_live_callback(
            label, self._translate, translate_key=False)

    def _translate(self, label, key, payload=None):
        translator = self.__translators[label]
        if payload is None:
            translator.translate_control_packet(MultiCastCommand(key))
        else:
            translator.translate_control_packet(MultiCastCommand(key, payload))
