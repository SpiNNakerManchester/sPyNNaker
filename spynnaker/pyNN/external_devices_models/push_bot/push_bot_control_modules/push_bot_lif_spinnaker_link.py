from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.models.neuron.implementations.defaults \
    import default_initial_values

import logging

logger = logging.getLogger(__name__)


class PushBotLifSpinnakerLink(ExternalDeviceLifControl):
    """ Control module for a pushbot connected to a SpiNNaker Link
    """
    __slots__ = []

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, protocol, devices,

            # default params for the neuron model type
            tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0, tau_syn_E=5.0,
            tau_syn_I=5.0, tau_refrac=0.1, i_offset=0.0, v=0.0,
            isyn_inh=0.0, isyn_exc=0.0):
        # pylint: disable=too-many-arguments, too-many-locals

        command_protocol = MunichIoSpiNNakerLinkProtocol(
            protocol.mode, uart_id=protocol.uart_id)
        for device in devices:
            device.set_command_protocol(command_protocol)

        # Initialise the abstract LIF class
        super(PushBotLifSpinnakerLink, self).__init__(
            devices, True, None, tau_m, cm, v_rest, v_reset,
            tau_syn_E, tau_syn_I, tau_refrac, i_offset, v, isyn_inh, isyn_exc)
