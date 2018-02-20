from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.external_devices_models import ExternalDeviceLifControl
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol

import logging

logger = logging.getLogger(__name__)


class PushBotLifSpinnakerLink(ExternalDeviceLifControl):
    """ Control module for a pushbot connected to a SpiNNaker Link
    """

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons, protocol, devices,

            # default params from abstract pop vertex
            spikes_per_second=AbstractPopulationVertex.
                non_pynn_default_parameters['spikes_per_second'],
            label=AbstractPopulationVertex.non_pynn_default_parameters[
                'label'],
            ring_buffer_sigma=AbstractPopulationVertex.
                non_pynn_default_parameters['ring_buffer_sigma'],
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
            tau_refrac=(
                ExternalDeviceLifControl.default_parameters['tau_refrac']
            ),
            i_offset=ExternalDeviceLifControl.default_parameters['i_offset'],
            v_init=initialize_parameters['v_init']):

        self._command_protocol = MunichIoSpiNNakerLinkProtocol(
            protocol.mode, uart_id=protocol.uart_id)
        for device in devices:
            device.set_command_protocol(self._command_protocol)

        # Initialise the abstract LIF class
        ExternalDeviceLifControl.__init__(
            self, n_neurons=n_neurons, devices=devices, create_edges=True,
            spikes_per_second=spikes_per_second, label=label,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            constraints=constraints,
            tau_m=tau_m, cm=cm, v_rest=v_rest, v_reset=v_reset,
            tau_syn_E=tau_syn_E, tau_syn_I=tau_syn_I,
            tau_refrac=tau_refrac, i_offset=i_offset, v_init=v_init
        )
