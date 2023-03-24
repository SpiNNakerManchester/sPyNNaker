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
from functools import partial
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import set_config
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, FPGAConnection)
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager)
from .spif_devices import (
    SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, SpiNNFPGARegister, set_distiller_key,
    set_distiller_mask_delayed, set_distiller_shift)

_MAX_INCOMING = 6


class SPIFOutputDevice(
        ApplicationFPGAVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex):
    """ Output (only) to a SPIF device.  Each SPIF device can accept up to 6
        incoming projections.
        Keys sent from Populations to SPIF will be mapped by removing the
        SpiNNaker key and adding an index so that the source Population can
        be identified.  Source Populations must be split into power-of-two
        sized cores to ensure that keys are contiguous.
        The keys output by SPIF will be of the form:
            |projection_index|neuron_id|
        By default, the projection index will be in the top 8 bits of the
        packet, but this can be controlled with the output_key_shift parameter.

    """

    __slots__ = ["__incoming_partitions", "__create_database",
                 "__output_key_shift"]

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

    def __is_power_of_2(self, v):
        """ Determine if a value is a power of 2

        :param int v: The value to test
        :rtype: bool
        """
        return (v & (v - 1) == 0) and (v != 0)

    @overrides(ApplicationFPGAVertex.add_incoming_edge)
    def add_incoming_edge(self, edge, partition):
        # Limit the number of incoming things
        if len(self.__incoming_partitions) == _MAX_INCOMING:
            raise ValueError(
                f"Only a maximum of {_MAX_INCOMING} connections are supported"
                " to each spif device")
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
        if self.__create_database:
            SpynnakerDataView.add_live_output_vertex(
                partition.pre_vertex, partition.identifier)

    def _get_set_xp_key_payload(self, index):
        """ Get the payload for the command to set the router key
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_first_key_from_pre_vertex(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier)

    def _get_set_xp_mask_payload(self, index):
        """ Get the payload for the command to set the router mask
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_routing_info_from_pre_vertex(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier).mask

    def _get_set_dist_mask_payload(self, index):
        """ Get the payload for the command to set the distiller mask
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return ~r_infos.get_routing_info_from_pre_vertex(
            self.__incoming_partitions[index].pre_vertex,
            self.__incoming_partitions[index].identifier).mask & 0xFFFFFFFF

    @property
    def start_resume_commands(self):
        # The commands here are delayed, as at the time of providing them,
        # we don't know the key or mask of the incoming link...
        for i in range(len(self.__incoming_partitions)):
            yield SpiNNFPGARegister.XP_KEY_0.delayed_command(
                self._get_set_xp_key_payload, index=i)
            yield SpiNNFPGARegister.XP_MASK_0.delayed_command(
                self._get_set_xp_mask_payload, index=i)
            yield set_distiller_key(i, i << self.__output_key_shift)
            yield set_distiller_mask_delayed(
                i, partial(self._get_set_dist_mask_payload, index=i))
            yield set_distiller_shift(
                i, self.__incoming_partitions[i].pre_vertex.n_colour_bits)

    @property
    def pause_stop_commands(self):
        return []

    @property
    def timed_commands(self):
        return []
