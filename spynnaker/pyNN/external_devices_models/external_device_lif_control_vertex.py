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
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractVertexWithEdgeToDependentVertices, HasCustomAtomKeyMap)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from .abstract_ethernet_controller import AbstractEthernetController


class ExternalDeviceLifControlVertex(
        AbstractPopulationVertex,
        AbstractEthernetController,
        AbstractVertexWithEdgeToDependentVertices,
        HasCustomAtomKeyMap):
    """ Abstract control module for the pushbot, based on the LIF neuron,\
        but without spikes, and using the voltage as the output to the various\
        devices
    """
    __slots__ = [
        "__dependent_vertices",
        "__devices",
        "__indices",
        "__message_translator"]

    # all commands will use this mask
    _DEFAULT_COMMAND_MASK = 0xFFFFFFFF

    def __init__(
            self, devices, create_edges, max_atoms_per_core, neuron_impl,
            pynn_model, translator=None, spikes_per_second=None, label=None,
            ring_buffer_sigma=None, incoming_spike_buffer_size=None,
            drop_late_spikes=None, splitter=None, seed=None,
            n_colour_bits=None):
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
        :param int n_colour_bits: The number of colour bits to use
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            len(devices), label, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            neuron_impl, pynn_model, drop_late_spikes, splitter, seed,
            n_colour_bits)

        if not devices:
            raise ConfigurationException("No devices specified")

        self.__devices = {dev.device_control_partition_id: dev
                          for dev in devices}
        self.__indices = {dev.device_control_partition_id: i
                          for i, dev in enumerate(devices)}
        self.__message_translator = translator

        # Add the edges to the devices if required
        self.__dependent_vertices = list()
        if create_edges:
            self.__dependent_vertices = devices

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices
               .edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        return [vertex.device_control_partition_id]

    @overrides(AbstractEthernetController.get_external_devices)
    def get_external_devices(self):
        return self.__devices.values()

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
        return list(self.__devices.keys())

    @overrides(HasCustomAtomKeyMap.get_atom_key_map)
    def get_atom_key_map(self, pre_vertex, partition_id, routing_info):
        index = self.__indices[partition_id]
        device = self.__devices[partition_id]
        return [(index, device.device_control_key)]

    @overrides(AbstractPopulationVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(self, partition_id):
        return BaseKeyAndMask(
            self.__devices[partition_id].device_control_key,
            self._DEFAULT_COMMAND_MASK)
