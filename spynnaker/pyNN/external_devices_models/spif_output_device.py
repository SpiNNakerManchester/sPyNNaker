# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import set_config
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, FPGAConnection)
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager)
from .spif_devices import (
    SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, SpiNNFPGARegister)


class SPIFOutputDevice(
        ApplicationFPGAVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex):
    """ Output (only) to a SPIF device
    """

    __slots__ = ["__incoming_partition", "__create_database"]

    def __init__(self, board_address=None, chip_coords=None, label=None,
                 create_database=True, database_notify_host=None,
                 database_notify_port_num=None, database_ack_port_num=None):
        super(SPIFOutputDevice, self).__init__(
            n_atoms=1,
            outgoing_fpga_connection=FPGAConnection(
                SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, board_address,
                chip_coords),
            label=label)
        self.__incoming_partition = None
        # Force creation of the database, to be used in the read side of things
        if create_database:
            set_config("Database", "create_database", "True")
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)
        self.__create_database = create_database

    @overrides(ApplicationFPGAVertex.add_incoming_edge)
    def add_incoming_edge(self, edge, partition):
        # Ignore non-spike partitions
        if partition.identifier != SPIKE_PARTITION_ID:
            return
        if self.__incoming_partition is not None:
            raise ValueError(
                "Only one outgoing connection is supported per spif device"
                f" (existing partition: {self.__incoming_partition}")
        self.__incoming_partition = partition
        if self.__create_database:
            SpynnakerDataView.add_live_output_vertex(
                self.__incoming_partition.pre_vertex,
                self.__incoming_partition.identifier)

    def _get_set_key_payload(self):
        """ Get the payload for the command to set the router key
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_first_key_from_pre_vertex(
            self.__incoming_partition.pre_vertex,
            self.__incoming_partition.identifier)

    def _get_set_mask_payload(self):
        """ Get the payload for the command to set the router mask
        """
        r_infos = SpynnakerDataView.get_routing_infos()
        return r_infos.get_routing_info_from_pre_vertex(
            self.__incoming_partition.pre_vertex,
            self.__incoming_partition.identifier).mask

    @property
    def start_resume_commands(self):
        # The commands here are delayed, as at the time of providing them,
        # we don't know the key or mask of the incoming link...
        return [
            SpiNNFPGARegister.P_KEY.delayed_command(
                self._get_set_key_payload),
            SpiNNFPGARegister.P_MASK.delayed_command(
                self._get_set_mask_payload)
        ]

    @property
    def pause_stop_commands(self):
        return []

    @property
    def timed_commands(self):
        return []
