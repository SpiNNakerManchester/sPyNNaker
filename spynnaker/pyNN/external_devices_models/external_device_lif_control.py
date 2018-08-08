from spinn_utilities.overrides import overrides

from .threshold_type_multicast_device_control \
    import ThresholdTypeMulticastDeviceControl
from .abstract_ethernet_controller import AbstractEthernetController

from pacman.model.constraints.key_allocator_constraints import \
    FixedKeyAndMaskConstraint
from pacman.model.routing_info import BaseKeyAndMask

from spinn_front_end_common.abstract_models import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models \
    import AbstractVertexWithEdgeToDependentVertices

from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential

import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)
_apv_defs = AbstractPopulationVertex.non_pynn_default_parameters


class ExternalDeviceLifControl(
        AbstractPopulationVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractEthernetController,
        AbstractVertexWithEdgeToDependentVertices):
    """ Abstract control module for the PushBot, based on the LIF neuron,\
        but without spikes, and using the voltage as the output to the various\
        devices
    """
    __slots__ = [
        "_dependent_vertices",
        "_devices",
        "_message_translator",
        "_partition_id_to_atom",
        "_partition_id_to_key"]

    _model_based_max_atoms_per_core = 15

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'v_rest': 0.0, 'v_reset': 0.0,
        'tau_syn_E': 5.0, 'tau_syn_I': 5.0, 'tau_refrac': 0.1, 'i_offset': 0,
        'isyn_exc': 0.0, 'isyn_inh': 0.0}

    initialize_parameters = {'v_init': None}

    # all commands will use this mask
    _DEFAULT_COMMAND_MASK = 0xFFFFFFFF

    def __init__(
            self, n_neurons, devices, create_edges, translator=None,

            # standard neuron stuff
            spikes_per_second=_apv_defs['spikes_per_second'],
            label=_apv_defs['label'],
            ring_buffer_sigma=_apv_defs['ring_buffer_sigma'],
            incoming_spike_buffer_size=_apv_defs['incoming_spike_buffer_size'],
            constraints=_apv_defs['constraints'],

            # default params for the neuron model type
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            tau_syn_E=default_parameters['tau_syn_E'],
            tau_syn_I=default_parameters['tau_syn_I'],
            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'],
            v_init=initialize_parameters['v_init'],
            isyn_inh=default_parameters['isyn_inh'],
            isyn_exc=default_parameters['isyn_exc']):
        """
        :param n_neurons: The number of neurons in the population
        :param devices:\
            The AbstractMulticastControllableDevice instances to be controlled\
            by the population
        :param create_edges:\
            True if edges to the devices should be added by this dev (set\
            to False if using the dev over Ethernet using a translator)
        :param translator:\
            Translator to be used when used for Ethernet communication.  Must\
            be provided if the dev is to be controlled over Ethernet.
        """
        # pylint: disable=too-many-arguments, too-many-locals

        if not devices:
            raise ConfigurationException("No devices specified")

        # Verify that there are the correct number of neurons
        if n_neurons != len(devices):
            raise ConfigurationException(
                "The number of neurons must match the number of devices")

        # Create a partition to key map
        self._partition_id_to_key = OrderedDict(
            (str(dev.device_control_partition_id), dev.device_control_key)
            for dev in devices)

        # Create a partition to atom map
        self._partition_id_to_atom = {
            partition: i
            for (i, partition) in enumerate(self._partition_id_to_key.keys())
        }

        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            n_neurons, tau_syn_E, tau_syn_I,
            initial_input_inh=isyn_inh,
            initial_input_exc=isyn_exc)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeMulticastDeviceControl(devices)

        self._devices = devices
        self._message_translator = translator

        # Add the edges to the devices if required
        self._dependent_vertices = list()
        if create_edges:
            self._dependent_vertices = devices

        super(ExternalDeviceLifControl, self).__init__(
            n_neurons=n_neurons, binary="external_device_lif_control.aplx",
            label=label,
            max_atoms_per_core=(
                ExternalDeviceLifControl._model_based_max_atoms_per_core),
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="ExternalDeviceLifControl",
            neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def get_max_atoms_per_core():
        return ExternalDeviceLifControl._model_based_max_atoms_per_core

    def routing_key_partition_atom_mapping(self, routing_info, partition):
        # pylint: disable=arguments-differ
        key = self._partition_id_to_key[partition.identifier]
        atom = self._partition_id_to_atom[partition.identifier]
        return [(atom, key)]

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [FixedKeyAndMaskConstraint([BaseKeyAndMask(
            self._partition_id_to_key[partition.identifier],
            self._DEFAULT_COMMAND_MASK)])]

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        return self._dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices
               .edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        return [vertex.device_control_partition_id]

    @overrides(AbstractEthernetController.get_external_devices)
    def get_external_devices(self):
        return self._devices

    @overrides(AbstractEthernetController.get_message_translator)
    def get_message_translator(self):
        if self._message_translator is None:
            raise ConfigurationException(
                "This population was not given a translator, and so cannot be"
                "used for Ethernet communication.  Please provide a "
                "translator for the population.")
        return self._message_translator

    @overrides(AbstractEthernetController.get_outgoing_partition_ids)
    def get_outgoing_partition_ids(self):
        return self._partition_id_to_key.keys()
