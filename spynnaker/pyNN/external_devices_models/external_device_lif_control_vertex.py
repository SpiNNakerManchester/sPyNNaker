# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from typing import Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationVirtualVertex)
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractVertexWithEdgeToDependentVertices, HasCustomAtomKeyMap)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from .abstract_ethernet_controller import AbstractEthernetController
from .abstract_multicast_controllable_device import (
    AbstractMulticastControllableDevice)
if TYPE_CHECKING:
    from pacman.model.graphs.machine.machine_vertex import MachineVertex
    from pacman.model.routing_info.routing_info import RoutingInfo
    from spynnaker.pyNN.models.neuron.implementations import AbstractNeuronImpl
    from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModel
    from .abstract_ethernet_translator import AbstractEthernetTranslator
    from spynnaker.pyNN.extra_algorithms.splitter_components import (
        SplitterAbstractPopulationVertex)


class ExternalDeviceLifControlVertex(
        AbstractPopulationVertex,
        AbstractEthernetController,
        AbstractVertexWithEdgeToDependentVertices,
        HasCustomAtomKeyMap):
    """
    Abstract control module for the pushbot, based on the LIF neuron, but
    without spikes, and using the voltage as the output to the various devices.
    """
    __slots__ = (
        "__dependent_vertices",
        "__devices",
        "__indices",
        "__message_translator")

    # all commands will use this mask
    _DEFAULT_COMMAND_MASK = 0xFFFFFFFF

    def __init__(
            self, *, devices: Sequence[AbstractMulticastControllableDevice],
            create_edges: bool, max_atoms_per_core: Tuple[int, ...],
            neuron_impl: AbstractNeuronImpl,
            pynn_model: AbstractPyNNNeuronModel,
            translator: Optional[AbstractEthernetTranslator] = None,
            spikes_per_second: Optional[float] = None,
            label: Optional[str] = None,
            ring_buffer_sigma: Optional[float] = None,
            max_expected_summed_weight: Optional[List[float]] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            drop_late_spikes: Optional[bool] = None,
            splitter: Optional[SplitterAbstractPopulationVertex] = None,
            seed: Optional[int] = None, n_colour_bits: Optional[int] = None):
        """
        :param list(AbstractMulticastControllableDevice) devices:
            The AbstractMulticastControllableDevice instances to be controlled
            by the population
        :param bool create_edges:
            True if edges to the devices should be added by this device (set
            to False if using the device over Ethernet using a translator)
        :param tuple(int, ...) max_atoms_per_core:
        :param AbstractNeuronImpl neuron_impl:
        :param AbstractPyNNNeuronModel pynn_model:
        :param translator:
            Translator to be used when used for Ethernet communication.  Must
            be provided if the device is to be controlled over Ethernet.
        :type translator: AbstractEthernetTranslator or None
        :param float spikes_per_second:
        :param str label:
        :param float ring_buffer_sigma:
        :param int incoming_spike_buffer_size:
        :param splitter: splitter from application vertices to machine vertices
        :type splitter: SplitterAbstractPopulationVertex or None
        :param int n_colour_bits: The number of colour bits to use
        """
        # pylint: disable=too-many-arguments
        if drop_late_spikes is None:
            drop_late_spikes = False
        super().__init__(
            n_neurons=len(devices),
            label=f"ext_dev{devices}" if label is None else label,
            max_atoms_per_core=max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            max_expected_summed_weight=max_expected_summed_weight,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            neuron_impl=neuron_impl, pynn_model=pynn_model,
            drop_late_spikes=drop_late_spikes, splitter=splitter, seed=seed,
            n_colour_bits=n_colour_bits)

        if not devices:
            raise ConfigurationException("No devices specified")

        self.__devices = {dev.device_control_partition_id: dev
                          for dev in devices}
        self.__indices = {dev.device_control_partition_id: i
                          for i, dev in enumerate(devices)}
        self.__message_translator = translator

        # Add the edges to the devices if required
        self.__dependent_vertices = (
            self.__dependents(devices) if create_edges else ())

    @staticmethod
    def __dependents(
            devices: Sequence[AbstractMulticastControllableDevice]) -> Tuple[
                ApplicationVirtualVertex, ...]:
        return tuple(
            dev for dev in devices
            if isinstance(dev, ApplicationVirtualVertex))

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self) -> Iterable[ApplicationVertex]:
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices
               .edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(
            self, vertex: ApplicationVertex) -> Iterable[str]:
        assert isinstance(vertex, AbstractMulticastControllableDevice)
        return [vertex.device_control_partition_id]

    @overrides(AbstractEthernetController.get_external_devices)
    def get_external_devices(self) -> Iterable[
            AbstractMulticastControllableDevice]:
        return self.__devices.values()

    @overrides(AbstractEthernetController.get_message_translator)
    def get_message_translator(self) -> AbstractEthernetTranslator:
        if self.__message_translator is None:
            raise ConfigurationException(
                "This population was not given a translator, and so cannot be"
                "used for Ethernet communication.  Please provide a "
                "translator for the population.")
        return self.__message_translator

    @overrides(AbstractEthernetController.get_outgoing_partition_ids)
    def get_outgoing_partition_ids(self) -> List[str]:
        return list(self.__devices.keys())

    @overrides(HasCustomAtomKeyMap.get_atom_key_map)
    def get_atom_key_map(
            self, pre_vertex: MachineVertex, partition_id: str,
            routing_info: RoutingInfo) -> Iterable[Tuple[int, int]]:
        index = self.__indices[partition_id]
        device = self.__devices[partition_id]
        return [(index, device.device_control_key)]

    @overrides(AbstractPopulationVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(
            self, partition_id: str) -> Optional[BaseKeyAndMask]:
        return BaseKeyAndMask(
            self.__devices[partition_id].device_control_key,
            self._DEFAULT_COMMAND_MASK)
