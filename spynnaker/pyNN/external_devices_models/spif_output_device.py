# Copyright (c) 2022 The University of Manchester
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

from typing import Dict, Iterable, Tuple, List

from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import set_config

from pacman.model.graphs.application import (
    ApplicationEdge, ApplicationEdgePartition, ApplicationFPGAVertex,
    FPGAConnection)
from pacman.model.graphs.machine import MachineVertex
from pacman.utilities.utility_calls import get_keys

from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex, LiveOutputDevice,
    HasCustomAtomKeyMap)
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utility_models import MultiCastCommand

from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager)

from .spif_devices import (
    SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK,
    set_distiller_key, set_distiller_mask,
    set_distiller_mask_delayed, set_distiller_shift,
    set_xp_key_delayed, set_xp_mask_delayed)

# The maximum number of partitions that can be supported.
N_OUTGOING = 6


class SPIFOutputDevice(
        ApplicationFPGAVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex, LiveOutputDevice):
    """
    Output (only) to a SPIF device.  Each SPIF device can accept up to 6
    incoming projections.
    Keys sent from Populations to SPIF will be mapped by removing the
    SpiNNaker key and adding an index so that the source Population can
    be identified.  Source Populations must be split into power-of-two
    sized cores to ensure that keys are contiguous.
    The keys output by SPIF will be of the form:

         (projection_index << output_key_shift) | neuron_id

    By default, the projection index will be in the top 8 bits of the
    packet, but this can be controlled with the output_key_shift parameter.
    """

    __slots__ = ("__incoming_partitions", "__create_database",
                 "__output_key_shift", "__output_key_and_mask")

    def __init__(self, board_address=None, chip_coords=None, label=None,
                 create_database=True, database_notify_host=None,
                 database_notify_port_num=None, database_ack_port_num=None,
                 output_key_shift=24):
        """
        :param board_address: The board IP address of the SPIF device
        :type board_address: int or None
        :param chip_coords: The chip coordinates of the SPIF device
        :type chip_coords: tuple(int, int) or None
        :param label: The label to give the SPIF device
        :type label: int or None
        :param bool create_database:
            Whether the database will be used to decode keys or not
        :param database_notify_host: The host that will read the database
        :type database_notify_host: str or None
        :param database_notify_port_num:
            The port of the host that will read the database
        :type database_notify_port_num: int or None
        :param database_ack_port_num:
            The port to listen on for responses from the host reading the
            database
        :type database_ack_port_num: int or None
        :param int proj_index_shift:
            The shift to apply to the population indices when added to the key
        """
        super(SPIFOutputDevice, self).__init__(
            n_atoms=1,
            outgoing_fpga_connection=FPGAConnection(
                SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, board_address,
                chip_coords),
            label=label)
        self.__incoming_partitions = list()
        # Force creation of the database, to be used in the read side of things
        if create_database:
            set_config("Database", "create_database", "True")
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)
        self.__create_database = create_database
        self.__output_key_shift = output_key_shift
        self.__output_key_and_mask = dict()

    def set_output_key_and_mask(self, population, key, mask):
        """ Set the output key to be written into packets when received by
            SPIF, and the mask to apply before adding the key.  The key should
            be the exact value that will be "or'ed" with the packet after
            masking.  The mask should be the mask to apply to the incoming
            SpiNNaker key to extract the neuron id bits.  The key and mask
            will not be checked; please make sure you are using values that
            make sense!

        :param Population population: The PyNN source Population
        :param int key: The key to "or" with the incoming key *after* masking
        :param int mask: The mask to "and" with the incoming SpiNNaker key
        """
        # pylint: disable=protected-access
        self.__output_key_and_mask[population._vertex] = (key, mask)

    def __is_power_of_2(self, v):
        """ Determine if a value is a power of 2.

        :param int v: The value to test
        :rtype: bool
        """
        return (v & (v - 1) == 0) and (v != 0)

    @overrides(ApplicationFPGAVertex.add_incoming_edge)
    def add_incoming_edge(
            self, edge: ApplicationEdge, partition: ApplicationEdgePartition):
        # Only add edges from PopulationApplicationVertices
        if not isinstance(edge.pre_vertex, PopulationApplicationVertex):
            if not isinstance(edge.pre_vertex, CommandSender):
                raise ValueError(
                    "This vertex only accepts input from "
                    "PopulationApplicationVertex instances")
            # Ignore the command sender sending to us!
            return

        if len(self.__incoming_partitions) >= N_OUTGOING:
            raise ValueError(
                f"Only {N_OUTGOING} outgoing connections are supported per"
                " spif device (existing partitions:"
                f" {self.__incoming_partitions}")
        # Ensure the incoming thing is split appropriately, as otherwise keys
        # won't be correct
        max_atoms = partition.pre_vertex.get_max_atoms_per_core()
        if max_atoms < partition.pre_vertex.n_atoms:
            if not self.__is_power_of_2(max_atoms):
                raise ValueError(
                    "The incoming vertex will be split into units of"
                    f" {max_atoms}, which means that the keys won't be"
                    " contiguous.  Please choose a power-of-two size for the"
                    " maximum atoms per core")
        self.__incoming_partitions.append(partition)
        if self.__create_database and len(self.__incoming_partitions) == 1:
            SpynnakerDataView.add_live_output_device(self)

    def _get_set_key_payload(self, index):
        """
        Get the payload for the command to set the router key.

        :param int index: The index of key to get
        :rtype: int
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_key_from(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier)

    def _get_set_mask_payload(self, index):
        """
        Get the payload for the command to set the router mask.

        :param int index: The index of the mask to get
        :rtype: int
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_info_from(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier).mask

    def _get_set_dist_mask_payload(self, index):
        """ Get the payload for the command to set the distiller mask
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return ~r_infos.get_info_from(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier).mask & 0xFFFFFFFF

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        # The commands here are delayed, as at the time of providing them,
        # we don't know the key or mask of the incoming link...
        commands = list()
        for i, part in enumerate(self.__incoming_partitions):
            commands.append(set_xp_key_delayed(i, self._get_set_key_payload))
            commands.append(set_xp_mask_delayed(i, self._get_set_mask_payload))
            if part.pre_vertex in self.__output_key_and_mask:
                key, mask = self.__output_key_and_mask[part.pre_vertex]
                commands.append(set_distiller_key(i, key))
                commands.append(set_distiller_mask(i, mask))
            else:
                commands.append(set_distiller_key(
                    i, i << self.__output_key_shift))
                commands.append(set_distiller_mask_delayed(
                    i, self._get_set_dist_mask_payload))
            commands.append(set_distiller_shift(
                i, part.pre_vertex.n_colour_bits))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        return []

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []

    @overrides(LiveOutputDevice.get_device_output_keys)
    def get_device_output_keys(self) -> Dict[MachineVertex,
                                             List[Tuple[int, int]]]:
        all_keys: Dict[MachineVertex, List[Tuple[int, int]]] = dict()
        routing_infos = SpynnakerDataView.get_routing_infos()
        for i, part in enumerate(self.__incoming_partitions):
            if part.pre_vertex in self.__output_key_and_mask:
                key, mask = self.__output_key_and_mask[part.pre_vertex]
            else:
                key = i << self.__output_key_shift
                mask = self._get_set_dist_mask_payload(i)
            shift = part.pre_vertex.n_colour_bits
            for m_vertex in part.pre_vertex.splitter.get_out_going_vertices(
                    part.identifier):
                atom_keys: Iterable[Tuple[int, int]] = list()
                if isinstance(m_vertex.app_vertex, HasCustomAtomKeyMap):
                    atom_keys = m_vertex.app_vertex.get_atom_key_map(
                        m_vertex, part.identifier, routing_infos)
                else:
                    r_info = \
                        routing_infos.get_info_from(
                            m_vertex, part.identifier)
                    vertex_slice = m_vertex.vertex_slice
                    keys = get_keys(r_info.key, vertex_slice)
                    start = vertex_slice.lo_atom
                    atom_keys = [(i, k) for i, k in enumerate(keys, start)]

                atom_keys_mapped = list((i, key | ((k & mask) >> shift))
                                        for i, k in atom_keys)
                all_keys[m_vertex] = atom_keys_mapped
        return all_keys
