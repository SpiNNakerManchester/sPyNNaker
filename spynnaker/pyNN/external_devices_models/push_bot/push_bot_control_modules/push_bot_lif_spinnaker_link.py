from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol

import logging

logger = logging.getLogger(__name__)
_abstract_defaults = AbstractPopulationVertex.non_pynn_default_parameters
_extern_defaults = ExternalDeviceLifControl.default_parameters


class PushBotLifSpinnakerLink(ExternalDeviceLifControl):
    """ Control module for a pushbot connected to a SpiNNaker Link
    """
    __slots__ = ["_command_protocol"]

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons, protocol, devices,

            # default params from abstract pop vertex
            spikes_per_second=_abstract_defaults['spikes_per_second'],
            label=_abstract_defaults['label'],
            ring_buffer_sigma=_abstract_defaults['ring_buffer_sigma'],
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

        self._command_protocol = MunichIoSpiNNakerLinkProtocol(
            protocol.mode, uart_id=protocol.uart_id)
        for device in devices:
            device.set_command_protocol(self._command_protocol)

        # Initialise the abstract LIF class
        super(PushBotLifSpinnakerLink, self).__init__(
            n_neurons=n_neurons, devices=devices, create_edges=True,
            spikes_per_second=spikes_per_second, label=label,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            constraints=constraints,
            tau_m=tau_m, cm=cm, v_rest=v_rest, v_reset=v_reset,
            tau_syn_E=tau_syn_E, tau_syn_I=tau_syn_I,
            tau_refrac=tau_refrac, i_offset=i_offset, v_init=v_init)
