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

from typing import Iterable, Optional, Union

from spinn_utilities.socket_address import SocketAddress
from spinn_utilities.config_holder import (get_config_int, get_config_str)

from spinnman.messages.eieio import EIEIOPrefix, EIEIOType

from pacman.model.graphs.application import (
    ApplicationEdge, ApplicationVertex)

from spinn_front_end_common.utility_models import (
    ReverseIpTagMultiCastSource)
from spinn_front_end_common.utilities.utility_objs import (
    LivePacketGatherParameters)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID, SPIKE_PARTITION_ID)


class SpynnakerExternalDevicePluginManager(object):
    """
    User-level interface for the external device plug-in manager.
    """
    __slots__ = ()

    @staticmethod
    def add_database_socket_address(
            database_notify_host: Optional[str],
            database_notify_port_num: Optional[int],
            database_ack_port_num: Optional[int]) -> None:
        """
        :param database_notify_host:
            Host to talk to tell that the database (and application) is ready.
        :param database_notify_port_num:
            Port to talk to tell that the database (and application) is ready.
        :param database_ack_port_num:
            Port on which to listen for an acknowledgement that the
            simulation should start.
        """
        # build the database socket address used by the notification interface
        database_socket = SocketAddress(
            listen_port=database_ack_port_num,
            notify_host_name=database_notify_host,
            notify_port_no=database_notify_port_num)

        # update socket interface with new demands.
        SpynnakerDataView.add_database_socket_address(database_socket)

    @staticmethod
    def activate_live_output_for(
            population: Population, *,
            database_notify_host: Optional[str] = None,
            database_notify_port_num: Optional[int] = None,
            database_ack_port_num: Optional[int] = None,
            port: Optional[int] = None, host: Optional[str] = None,
            tag: Optional[int] = None, strip_sdp: bool = True,
            use_prefix: bool = False, key_prefix: Optional[int] = None,
            prefix_type: Optional[EIEIOPrefix] = None,
            message_type: EIEIOType = EIEIOType.KEY_32_BIT,
            right_shift: int = 0, payload_as_time_stamps: bool = True,
            notify: bool = True, use_payload_prefix: bool = True,
            payload_prefix: Optional[int] = None, payload_right_shift: int = 0,
            number_of_packets_sent_per_time_step: int = 0,
            translate_keys: bool = False,
            partition_ids: Optional[Iterable[str]] = None) -> None:
        """
        Output the spikes from a given population from SpiNNaker as they
        occur in the simulation.

        :param population: The population to activate the live output for
        :param database_notify_host:
            The hostname for the device which is listening to the database
            notification.
        :param database_ack_port_num:
            The port number to which a external device will acknowledge that
            they have finished reading the database and are ready for it to
            start execution
        :param database_notify_port_num:
            The port number to which a external device will receive the
            database is ready command
        :param key_prefix: the prefix to be applied to the key
        :param prefix_type:
            if the prefix type is 32 bit or 16 bit
        :param message_type:
            If the message is a EIEIO command message, or an EIEIO data
            message with 16 bit or 32 bit keys.
        :param payload_as_time_stamps:
        :param right_shift:
        :param use_payload_prefix:
        :param notify:
        :param payload_prefix:
        :param payload_right_shift:
        :param number_of_packets_sent_per_time_step:
        :param port:
            The UDP port to which the live spikes will be sent. If not
            specified, the port will be taken from the "live_spike_port"
            parameter in the "Recording" section of the sPyNNaker
            configuration file.
        :param host:
            The host name or IP address to which the live spikes will be
            sent. If not specified, the host will be taken from the
            "live_spike_host" parameter in the "Recording" section of the
            sPyNNaker configuration file.
        :param tag:
            The IP tag to be used for the spikes. If not specified, one will
            be automatically assigned
        :param strip_sdp:
            Determines if the SDP headers will be stripped from the
            transmitted packet.
        :param use_prefix:
            Determines if the spike packet will contain a common prefix for
            the spikes
        :param partition_ids:
            The names of the partitions to create edges for
        :param translate_keys:
            Whether the incoming keys from the cores should be translated
            to global keys rather than core-based keys
        """
        # pylint: disable=protected-access
        # get default params if none set
        if port is None:
            port = get_config_int("Recording", "live_spike_port")
        if host is None:
            host = get_config_str("Recording", "live_spike_host")

        # Use the right-shift to remove the colour from translated keys
        n_colour_bits = population._vertex.n_colour_bits
        translated_key_right_shift = n_colour_bits

        # Use the mask to remove the colour from non-translated keys
        received_key_mask = 0xFFFFFFFF & ~((2 ** n_colour_bits) - 1)

        if partition_ids is None:
            partition_ids = [SPIKE_PARTITION_ID]

        params = LivePacketGatherParameters(
            port=port, hostname=host, tag=tag, strip_sdp=strip_sdp,
            use_prefix=use_prefix, key_prefix=key_prefix,
            prefix_type=prefix_type, message_type=message_type,
            right_shift=right_shift, payload_prefix=payload_prefix,
            payload_as_time_stamps=payload_as_time_stamps,
            use_payload_prefix=use_payload_prefix,
            payload_right_shift=payload_right_shift,
            number_of_packets_sent_per_time_step=(
                number_of_packets_sent_per_time_step),
            label="LiveSpikeReceiver", received_key_mask=received_key_mask,
            translate_keys=translate_keys,
            translated_key_right_shift=translated_key_right_shift)
        SpynnakerExternalDevicePluginManager.update_live_packet_gather_tracker(
            population._vertex, params, partition_ids)

        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def activate_live_output_to(
            population: Population,
            device: Union[Population, ApplicationVertex],
            partition_id: str = SPIKE_PARTITION_ID) -> None:
        """
        Activate the output of spikes from a population to an external device.

        .. note::
            All spikes will be sent to the device.

        :param population:
            The pyNN population object from which spikes will be sent.
        :param device:
            The pyNN population or external device to which the spikes will be
            sent.
        :param partition_id:
            The partition ID to activate live output to.
        """
        # pylint: disable=protected-access
        if isinstance(device, Population):
            device_vertex: ApplicationVertex = device._vertex
        else:
            device_vertex = device
        SpynnakerExternalDevicePluginManager.add_edge(
            population._vertex, device_vertex, partition_id)

    @staticmethod
    def update_live_packet_gather_tracker(
            vertex_to_record_from: ApplicationVertex,
            params: LivePacketGatherParameters,
            partition_ids: Iterable[str]) -> None:
        """
        Add an edge from a vertex to the live packet gatherer, builds as
        needed and has all the parameters for the creation of the live
        packet gatherer if needed.

        :param vertex_to_record_from:
        :param params:
        :param partition_ids:
        """
        # add to the tracker
        SpynnakerDataView.add_live_packet_gatherer_parameters(
            params, vertex_to_record_from, partition_ids)

    @staticmethod
    def add_poisson_live_rate_control(
            poisson_population: Population, *,
            control_label_extension: str = "_control",
            receive_port: Optional[int] = None,
            database_notify_host: Optional[str] = None,
            database_notify_port_num: Optional[int] = None,
            database_ack_port_num: Optional[int] = None, notify: bool = True,
            reserve_reverse_ip_tag: bool = False) -> None:
        """
        Add a live rate controller to a Poisson population.

        :param poisson_population: The population to control
        :param control_label_extension:
            An extension to add to the label of the Poisson source. Must match
            up with the equivalent in the SpynnakerPoissonControlConnection
        :param receive_port:
            The port that the SpiNNaker board should listen on
        :param database_notify_host: the hostname for the device which is
            listening to the database notification.
        :param database_ack_port_num: the port number to which a external
            device will acknowledge that they have finished reading the
            database and are ready for it to start execution
        :param database_notify_port_num: The port number to which an
            external device will receive the database is ready command
        :param notify: adds to the notification protocol if set.
        :param reserve_reverse_ip_tag: True if a reverse IP tag is to be
            used, False if SDP is to be used (default)
        """
        # pylint: disable=protected-access
        vertex = poisson_population._vertex
        if not isinstance(vertex, SpikeSourcePoissonVertex):
            raise TypeError("population must contain a SpikeSourcePoisson")
        control_label = f"{vertex.label}{control_label_extension}"
        controller = ReverseIpTagMultiCastSource(
            n_keys=vertex.n_atoms, label=control_label,
            receive_port=receive_port,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag)
        SpynnakerExternalDevicePluginManager.add_application_vertex(controller)
        edge = SpynnakerExternalDevicePluginManager.add_edge(
            controller, vertex, LIVE_POISSON_CONTROL_PARTITION_ID)
        vertex.set_live_poisson_control_edge(edge)
        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def add_edge(vertex: ApplicationVertex, device_vertex: ApplicationVertex,
                 partition_id: str) -> ApplicationEdge:
        """
        Add an edge between two vertices (often a vertex and a external
        device) on a given partition.

        :param vertex:
            the pre-population vertex to connect the edge from
        :param device_vertex:
            the post-population vertex to connect the edge to
        :param partition_id: the partition identifier for making nets
        """
        edge = ApplicationEdge(vertex, device_vertex)
        SpynnakerDataView.add_edge(edge, partition_id)
        return edge

    @staticmethod
    def add_application_vertex(vertex: ApplicationVertex) -> None:
        """
        Adds an Application vertex to the user graph.

        Semantic sugar for SpynnakerDataView.add_vertex(vertex)

        :param vertex:
        """
        SpynnakerDataView.add_vertex(vertex)
