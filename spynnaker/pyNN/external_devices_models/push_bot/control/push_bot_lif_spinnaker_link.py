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
