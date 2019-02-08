from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import (
        PushBotTranslator)
from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import (
        get_pushbot_wifi_connection)


class PushBotLifEthernet(ExternalDeviceLifControl):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input
    """
    __slots__ = []

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, protocol, devices, pushbot_ip_address,
            pushbot_port=56000,

            # default params for the neuron model type
            tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0, tau_syn_E=5.0,
            tau_syn_I=5.0, tau_refrac=0.1, i_offset=0.0, v=0.0,
            isyn_inh=0.0, isyn_exc=0.0):
        # pylint: disable=too-many-arguments, too-many-locals

        translator = PushBotTranslator(
            protocol,
            get_pushbot_wifi_connection(pushbot_ip_address, pushbot_port))

        super(PushBotLifEthernet, self).__init__(
            devices, False, translator, tau_m, cm, v_rest, v_reset,
            tau_syn_E, tau_syn_I, tau_refrac, i_offset, v, isyn_inh, isyn_exc)
