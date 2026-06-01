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

from typing import Iterable

from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotEthernetDevice)
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.models.defaults import default_initial_values


class PushBotLifSpinnakerLink(ExternalDeviceLifControl):
    """
    Control module for a PushBot connected to a SpiNNaker Link.

    :param protocol: How to talk to the bot.
    :param devices: The devices on the bot that we are interested in.
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
            devices: Iterable[PushBotEthernetDevice],

            # default params for the neuron model type
            tau_m: float = 20.0, cm: float = 1.0, v_rest: float = 0.0,
            v_reset: float = 0.0, tau_syn_E: float = 5.0,
            tau_syn_I: float = 5.0, tau_refrac: float = 0.1,
            i_offset: float = 0.0, v: float = 0.0, isyn_exc: float = 0.0,
            isyn_inh: float = 0.0):
        """
        :param protocol: Protocol to set on the devices
        :param devices:
            The AbstractMulticastControllableDevice instances to be controlled
            by the population
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
        command_protocol = MunichIoSpiNNakerLinkProtocol(
            protocol.mode, uart_id=protocol.uart_id)
        for device in devices:
            device.set_command_protocol(command_protocol)

        # Initialise the abstract LIF class
        super().__init__(
            devices, True, None, tau_m, cm, v_rest, v_reset,
            tau_syn_E, tau_syn_I, tau_refrac, i_offset, v, isyn_exc, isyn_inh)
