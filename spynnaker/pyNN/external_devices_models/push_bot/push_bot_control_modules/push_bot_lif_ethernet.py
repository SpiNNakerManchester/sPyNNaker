from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import PushBotTranslator
from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import get_pushbot_wifi_connection

_abstract_defaults = AbstractPopulationVertex.non_pynn_default_parameters
_extern_defaults = ExternalDeviceLifControl.default_parameters


class PushBotLifEthernet(ExternalDeviceLifControl):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input
    """
    __slots__ = []

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons, protocol, devices, pushbot_ip_address,
            pushbot_port=56000,
            spikes_per_second=_abstract_defaults['spikes_per_second'],
            ring_buffer_sigma=_abstract_defaults['ring_buffer_sigma'],
            label=_abstract_defaults['label'],
            incoming_spike_buffer_size=_abstract_defaults[
                'incoming_spike_buffer_size'],
            constraints=_abstract_defaults['constraints'],

            # default params for the neuron model type
            tau_m=_extern_defaults['tau_m'],
            cm=_extern_defaults['cm'],
            v_rest=_extern_defaults['v_rest'],
            v_reset=_extern_defaults['v_reset'],
            tau_syn_E=_extern_defaults['tau_syn_E'],
            tau_syn_I=_extern_defaults['tau_syn_I'],
            tau_refrac=_extern_defaults['tau_refrac'],
            i_offset=_extern_defaults['i_offset'],
            v_init=initialize_parameters['v_init']):
        # pylint: disable=too-many-arguments, too-many-locals

        translator = PushBotTranslator(
            protocol,
            get_pushbot_wifi_connection(pushbot_ip_address, pushbot_port))

        super(PushBotLifEthernet, self).__init__(
            n_neurons, devices, False, translator, spikes_per_second,
            label, ring_buffer_sigma, incoming_spike_buffer_size, constraints,
            tau_m, cm, v_rest, v_reset, tau_syn_E, tau_syn_I, tau_refrac,
            i_offset, v_init)
