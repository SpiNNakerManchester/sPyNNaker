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

from typing import List

from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotTranslator)
from spynnaker.pyNN.external_devices_models import (
    AbstractMulticastControllableDevice, ExternalDeviceLifControl)
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    get_pushbot_wifi_connection)
from spynnaker.pyNN.protocols.munich_io_spinnaker_link_protocol import (
    MunichIoSpiNNakerLinkProtocol)


class PushBotLifEthernet(ExternalDeviceLifControl):
    """
    Leaky integrate and fire neuron with an exponentially decaying
    current input.

    :param protocol: How to talk to the bot.
    :param devices: The devices on the bot that we are interested in.
    :param pushbot_ip_address: Where is the pushbot?
    :param pushbot_port: (defaulted)
    :param tau_m: LIF neuron parameter (defaulted)
    :param cm: LIF neuron parameter (defaulted)
    :param v_rest: LIF neuron parameter (defaulted)
    :param v_reset: LIF neuron parameter (defaulted)
    :param tau_syn_E: LIF neuron parameter (defaulted)
    :param tau_syn_I: LIF neuron parameter (defaulted)
    :param tau_refrac: LIF neuron parameter (defaulted)
    :param i_offset: LIF neuron parameter (defaulted)
    :param v: LIF neuron parameter (defaulted)
    :param isyn_exc: LIF neuron parameter (defaulted)
    :param isyn_inh: LIF neuron parameter (defaulted)
    """
    __slots__ = ()

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, protocol: MunichIoSpiNNakerLinkProtocol,
            devices: List[AbstractMulticastControllableDevice],
            pushbot_ip_address: str, pushbot_port: int = 56000,
            # default params for the neuron model type
            tau_m: float = 20.0, cm: float = 1.0, v_rest: float = 0.0,
            v_reset: float = 0.0, tau_syn_E: float = 5.0,
            tau_syn_I: float = 5.0, tau_refrac: float = 0.1,
            i_offset: float = 0.0, v: float = 0.0, isyn_exc: float = 0.0,
            isyn_inh: float = 0.0):
        """
        :param protocol:
           The instance of the PushBot protocol to get keys from
        :param devices:
            The AbstractMulticastControllableDevice instances to be controlled
            by the population
        :param pushbot_ip_address: The IP address of the PushBot
        :param pushbot_port:
        :param tau_m: (defaulted LIF neuron parameter)
        :param cm: (defaulted LIF neuron parameter)
        :param v_rest: (defaulted LIF neuron parameter)
        :param v_reset: (defaulted LIF neuron parameter)
        :param tau_syn_E: (defaulted LIF neuron parameter)
        :param tau_syn_I: (defaulted LIF neuron parameter)
        :param tau_refrac: (defaulted LIF neuron parameter)
        :param i_offset: (defaulted LIF neuron parameter)
        :param v: (defaulted LIF neuron state variable initial value)
        :param isyn_exc:
            (defaulted LIF neuron state variable initial value)
        :param isyn_inh:
            (defaulted LIF neuron state variable initial value)

        """
        translator = PushBotTranslator(
            protocol,
            get_pushbot_wifi_connection(pushbot_ip_address, pushbot_port))

        super().__init__(
            devices, False, translator, tau_m, cm, v_rest, v_reset,
            tau_syn_E, tau_syn_I, tau_refrac, i_offset, v, isyn_exc, isyn_inh)
