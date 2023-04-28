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

from spinn_utilities.socket_address import SocketAddress
from pacman.model.graphs.application import ApplicationEdge
from spinn_utilities.config_holder import (get_config_int, get_config_str)
from spinnman.messages.eieio import EIEIOType
from spinn_front_end_common.utility_models import (
    ReverseIpTagMultiCastSource)
from spinn_front_end_common.utilities.utility_objs import (
    LivePacketGatherParameters)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID, SPIKE_PARTITION_ID)
from spynnaker.pyNN.models.populations import Population


class SpynnakerExternalDevicePluginManager(object):
    """
    User-level interface for the external device plug-in manager.
    """
    __slots__ = []

    @staticmethod
    def add_database_socket_address(
            database_notify_host, database_notify_port_num,
            database_ack_port_num):
        """
        :param database_notify_host:
            Host to talk to tell that the database (and application) is ready.
        :type database_notify_host: str or None
        :param database_notify_port_num:
            Port to talk to tell that the database (and application) is ready.
        :type database_notify_port_num: int or None
        :param database_ack_port_num:
            Port on which to listen for an acknowledgement that the
            simulation should start.
        :type database_ack_port_num: int or None
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
            population, database_notify_host=None,
            database_notify_port_num=None,
            database_ack_port_num=None, port=None, host=None, tag=None,
            strip_sdp=True, use_prefix=False, key_prefix=None,
            prefix_type=None, message_type=EIEIOType.KEY_32_BIT,
            right_shift=0, payload_as_time_stamps=True, notify=True,
            use_payload_prefix=True, payload_prefix=None,
            payload_right_shift=0, number_of_packets_sent_per_time_step=0,
            translate_keys=False):
        """
        Output the spikes from a given population from SpiNNaker as they
        occur in the simulation.

        :param ~spynnaker.pyNN.models.populations.Population population:
            The population to activate the live output for
        :param str database_notify_host:
            The hostname for the device which is listening to the database
            notification.
        :param int database_ack_port_num:
            The port number to which a external device will acknowledge that
            they have finished reading the database and are ready for it to
            start execution
        :param int database_notify_port_num:
            The port number to which a external device will receive the
            database is ready command
        :param key_prefix: the prefix to be applied to the key
        :type key_prefix: int or None
        :param ~spinnman.messages.eieio.EIEIOPrefix prefix_type:
            if the prefix type is 32 bit or 16 bit
        :param ~spinnman.messages.eieio.EIEIOType message_type:
            If the message is a EIEIO command message, or an EIEIO data
            message with 16 bit or 32 bit keys.
        :param bool payload_as_time_stamps:
        :param int right_shift:
        :param bool use_payload_prefix:
        :param bool notify:
        :param payload_prefix:
        :type payload_prefix: int or None
        :param int payload_right_shift:
        :param int number_of_packets_sent_per_time_step:
        :param int port:
            The UDP port to which the live spikes will be sent. If not
            specified, the port will be taken from the "live_spike_port"
            parameter in the "Recording" section of the sPyNNaker
            configuration file.
        :param str host:
            The host name or IP address to which the live spikes will be
            sent. If not specified, the host will be taken from the
            "live_spike_host" parameter in the "Recording" section of the
            sPyNNaker configuration file.
        :param int tag:
            The IP tag to be used for the spikes. If not specified, one will
            be automatically assigned
        :param bool strip_sdp:
            Determines if the SDP headers will be stripped from the
            transmitted packet.
        :param bool use_prefix:
            Determines if the spike packet will contain a common prefix for
            the spikes
        :param str label: The label of the gatherer vertex
        :param list(str) partition_ids:
            The names of the partitions to create edges for
        :param bool translate_keys:
            Whether the incoming keys from the cores should be translated
            to global keys rather than core-based keys
        """
        # pylint: disable=too-many-arguments, too-many-locals, protected-access
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

        # pylint: disable=too-many-arguments, too-many-locals
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
            population._vertex, params, [SPIKE_PARTITION_ID])

        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def activate_live_output_to(
            population, device, partition_id=SPIKE_PARTITION_ID):
        """
        Activate the output of spikes from a population to an external device.

        .. note::
            All spikes will be sent to the device.

        :param ~spynnaker.pyNN.models.populations.Population population:
            The pyNN population object from which spikes will be sent.
        :param device:
            The pyNN population or external device to which the spikes will be
            sent.
        :type device:
            ~spynnaker.pyNN.models.populations.Population or
            ~pacman.model.graphs.application.ApplicationVertex
        :param str partition_id:
            The partition ID to activate live output to.
        """
        device_vertex = device
        # pylint: disable=protected-access
        if isinstance(device, Population):
            device_vertex = device._vertex
        SpynnakerExternalDevicePluginManager.add_edge(
            population._vertex, device_vertex, partition_id)

    @staticmethod
    def update_live_packet_gather_tracker(
            vertex_to_record_from, params, partition_ids):
        """
        Add an edge from a vertex to the live packet gatherer, builds as
        needed and has all the parameters for the creation of the live
        packet gatherer if needed.

        :param vertex_to_record_from:
        :type vertex_to_record_from:
            ~pacman.model.graphs.application.ApplicationVertex or
            ~pacman.model.graphs.machine.MachineVertex
        :param params:
        :type params:
             ~spinn_front_end_common.utilities.utility_objs.LivePacketGatherParameters
        :param list(str) partition_ids:
        :param bool translate_keys:
        """
        # add to the tracker
        SpynnakerDataView.add_live_packet_gatherer_parameters(
            params, vertex_to_record_from, partition_ids)

    @staticmethod
    def add_poisson_live_rate_control(
            poisson_population, control_label_extension="_control",
            receive_port=None, database_notify_host=None,
            database_notify_port_num=None,
            database_ack_port_num=None, notify=True,
            reserve_reverse_ip_tag=False):
        """
        Add a live rate controller to a Poisson population.

        :param poisson_population: The population to control
        :type poisson_population:
            ~spynnaker.pyNN.models.populations.Population
        :param str control_label_extension:
            An extension to add to the label of the Poisson source. Must match
            up with the equivalent in the SpynnakerPoissonControlConnection
        :param int receive_port:
            The port that the SpiNNaker board should listen on
        :param str database_notify_host: the hostname for the device which is
            listening to the database notification.
        :param int database_ack_port_num: the port number to which a external
            device will acknowledge that they have finished reading the
            database and are ready for it to start execution
        :param int database_notify_port_num: The port number to which an
            external device will receive the database is ready command
        :param bool notify: adds to the notification protocol if set.
        :param bool reserve_reverse_ip_tag: True if a reverse IP tag is to be
            used, False if SDP is to be used (default)
        """
        # pylint: disable=too-many-arguments, protected-access
        vertex = poisson_population._vertex
        control_label = f"{vertex.label}{control_label_extension}"
        controller = ReverseIpTagMultiCastSource(
            n_keys=vertex.n_atoms, label=control_label,
            receive_port=receive_port,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag,
            injection_partition_id=LIVE_POISSON_CONTROL_PARTITION_ID)
        SpynnakerExternalDevicePluginManager.add_application_vertex(controller)
        edge = SpynnakerExternalDevicePluginManager.add_edge(
            controller, vertex, LIVE_POISSON_CONTROL_PARTITION_ID)
        vertex.set_live_poisson_control_edge(edge)
        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def add_edge(vertex, device_vertex, partition_id):
        """
        Add an edge between two vertices (often a vertex and a external
        device) on a given partition.

        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            the pre-population vertex to connect the edge from
        :param device_vertex:
            the post-population vertex to connect the edge to
        :type device_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str partition_id: the partition identifier for making nets
        """
        edge = ApplicationEdge(vertex, device_vertex)
        SpynnakerDataView.add_edge(edge, partition_id)
        return edge

    @staticmethod
    def add_application_vertex(vertex):
        SpynnakerDataView.add_vertex(vertex)
