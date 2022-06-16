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

from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractVertexWithEdgeToDependentVertices)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from .abstract_ethernet_controller import AbstractEthernetController


class ExternalDeviceLifControlVertex(
        AbstractPopulationVertex,
        AbstractEthernetController,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractVertexWithEdgeToDependentVertices):
    """ Abstract control module for the pushbot, based on the LIF neuron,\
        but without spikes, and using the voltage as the output to the various\
        devices
    """
    __slots__ = [
        "__dependent_vertices",
        "__devices",
        "__message_translator",
        "__partition_id_to_atom",
        "__partition_id_to_key"]

    # all commands will use this mask
    _DEFAULT_COMMAND_MASK = 0xFFFFFFFF

    def __init__(
            self, devices, create_edges, max_atoms_per_core, neuron_impl,
            pynn_model, translator=None, spikes_per_second=None, label=None,
            ring_buffer_sigma=None, incoming_spike_buffer_size=None,
            drop_late_spikes=None, constraints=None, splitter=None,
            min_weights=None, weight_random_sigma=None,
            max_stdp_spike_delta=None):
        """
        :param list(AbstractMulticastControllableDevice) devices:
            The AbstractMulticastControllableDevice instances to be controlled
            by the population
        :param bool create_edges:
            True if edges to the devices should be added by this dev (set
            to False if using the dev over Ethernet using a translator)
        :param int max_atoms_per_core:
        :param AbstractNeuronImpl neuron_impl:
        :param pynn_model:
        :param translator:
            Translator to be used when used for Ethernet communication.  Must
            be provided if the dev is to be controlled over Ethernet.
        :type translator: AbstractEthernetTranslator or None
        :param float spikes_per_second:
        :param str label:
        :param float ring_buffer_sigma:
        :param int incoming_spike_buffer_size:
        :param splitter: splitter from app to machine
        :type splitter: None or
            ~pacman.model.partitioner_splitters.abstract_splitters.AbstractSplitterCommon
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
        :param list min_weights:
        :param float weight_random_sigma:
        :param float max_stdp_spike_delta:
        """
        # pylint: disable=too-many-arguments

        if not devices:
            raise ConfigurationException("No devices specified")

        # Create a partition to key map
        self.__partition_id_to_key = dict(
            (str(dev.device_control_partition_id), dev.device_control_key)
            for dev in devices)

        # Check for same partition name
        if len(self.__partition_id_to_key) != len(devices):
            raise Exception(
                "Partition names for each device must be different")

        # Create a partition to atom map
        self.__partition_id_to_atom = {
            partition: i
            for (i, partition) in enumerate(self.__partition_id_to_key.keys())
        }

        self.__devices = devices
        self.__message_translator = translator

        # Add the edges to the devices if required
        self.__dependent_vertices = list()
        if create_edges:
            self.__dependent_vertices = devices

        super().__init__(
            len(devices), label, constraints, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma,
            incoming_spike_buffer_size, neuron_impl, pynn_model,
            drop_late_spikes, splitter, min_weights,
            weight_random_sigma, max_stdp_spike_delta)

    def routing_key_partition_atom_mapping(self, routing_info, partition):
        key = self.__partition_id_to_key[partition.identifier]
        atom = self.__partition_id_to_atom[partition.identifier]
        return [(atom, key)]

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [FixedKeyAndMaskConstraint([BaseKeyAndMask(
            self.__partition_id_to_key[partition.identifier],
            self._DEFAULT_COMMAND_MASK)])]

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices
               .edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        return [vertex.device_control_partition_id]

    @overrides(AbstractEthernetController.get_external_devices)
    def get_external_devices(self):
        return self.__devices

    @overrides(AbstractEthernetController.get_message_translator)
    def get_message_translator(self):
        if self.__message_translator is None:
            raise ConfigurationException(
                "This population was not given a translator, and so cannot be"
                "used for Ethernet communication.  Please provide a "
                "translator for the population.")
        return self.__message_translator

    @overrides(AbstractEthernetController.get_outgoing_partition_ids)
    def get_outgoing_partition_ids(self):
        return self.__partition_id_to_key.keys()
