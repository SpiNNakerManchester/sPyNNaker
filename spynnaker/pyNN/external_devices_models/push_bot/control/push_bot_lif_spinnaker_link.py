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

from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.models.defaults import default_initial_values


class PushBotLifSpinnakerLink(ExternalDeviceLifControl):
    """ Control module for a PushBot connected to a SpiNNaker Link

    :param ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol protocol:
        How to talk to the bot.
    :param iterable(AbstractMulticastControllableDevice) devices:
        The devices on the bot that we are interested in.
    :param float tau_m: LIF neuron parameter (defaulted)
    :param float cm: LIF neuron parameter (defaulted)
    :param float v_rest: LIF neuron parameter (defaulted)
    :param float v_reset: LIF neuron parameter (defaulted)
    :param float tau_syn_E: LIF neuron parameter (defaulted)
    :param float tau_syn_I: LIF neuron parameter (defaulted)
    :param float tau_refrac: LIF neuron parameter (defaulted)
    :param float i_offset: LIF neuron parameter (defaulted)
    :param float v: LIF neuron parameter (defaulted)
    :param float isyn_exc: LIF neuron parameter (defaulted)
    :param float isyn_inh: LIF neuron parameter (defaulted)
    """
    __slots__ = []

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, protocol, devices,

            # default params for the neuron model type
            tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0, tau_syn_E=5.0,
            tau_syn_I=5.0, tau_refrac=0.1, i_offset=0.0, v=0.0,
            isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments

        command_protocol = MunichIoSpiNNakerLinkProtocol(
            protocol.mode, uart_id=protocol.uart_id)
        for device in devices:
            device.set_command_protocol(command_protocol)

        # Initialise the abstract LIF class
        super().__init__(
            devices, True, None, tau_m, cm, v_rest, v_reset,
            tau_syn_E, tau_syn_I, tau_refrac, i_offset, v, isyn_exc, isyn_inh)
