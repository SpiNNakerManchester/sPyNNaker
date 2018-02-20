from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import PushBotTranslator
from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import get_pushbot_wifi_connection


class PushBotLifEthernet(ExternalDeviceLifControl):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input
    """

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons, protocol, devices, pushbot_ip_address,
            pushbot_port=56000,
            spikes_per_second=AbstractPopulationVertex.
            non_pynn_default_parameters['spikes_per_second'],
            ring_buffer_sigma=AbstractPopulationVertex.
            non_pynn_default_parameters['ring_buffer_sigma'],
            label=AbstractPopulationVertex.
            non_pynn_default_parameters['label'],
            incoming_spike_buffer_size=AbstractPopulationVertex.
            non_pynn_default_parameters['incoming_spike_buffer_size'],
            constraints=AbstractPopulationVertex.
            non_pynn_default_parameters['constraints'],

            # default params for the neuron model type
            tau_m=ExternalDeviceLifControl.default_parameters['tau_m'],
            cm=ExternalDeviceLifControl.default_parameters['cm'],
            v_rest=ExternalDeviceLifControl.default_parameters['v_rest'],
            v_reset=ExternalDeviceLifControl.default_parameters['v_reset'],
            tau_syn_E=ExternalDeviceLifControl.default_parameters['tau_syn_E'],
            tau_syn_I=ExternalDeviceLifControl.default_parameters['tau_syn_I'],
            tau_refrac=ExternalDeviceLifControl.default_parameters[
                'tau_refrac'],
            i_offset=ExternalDeviceLifControl.default_parameters['i_offset'],
            v_init=initialize_parameters['v_init']):

        translator = PushBotTranslator(
            protocol,
            get_pushbot_wifi_connection(pushbot_ip_address, pushbot_port))

        ExternalDeviceLifControl.__init__(
            self, n_neurons, devices, False, translator, spikes_per_second,
            label, ring_buffer_sigma, incoming_spike_buffer_size, constraints,
            tau_m, cm, v_rest, v_reset, tau_syn_E, tau_syn_I, tau_refrac,
            i_offset, v_init)
