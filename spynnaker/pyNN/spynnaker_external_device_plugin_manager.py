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

from spinn_utilities.socket_address import SocketAddress
from pacman.model.graphs.application import ApplicationEdge
from spinn_utilities.config_holder import (get_config_int, get_config_str)
from spinnman.messages.eieio import EIEIOType
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spinn_front_end_common.utility_models import (
    ReverseIpTagMultiCastSource)
from spinn_front_end_common.utilities.utility_objs import (
    LivePacketGatherParameters)
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID, SPIKE_PARTITION_ID)
from spynnaker.pyNN.models.populations import Population


class SpynnakerExternalDevicePluginManager(object):
    """ User-level interface for the external device plugin manager.
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
        if database_notify_port_num is None:
            database_notify_port_num = get_config_int(
                "Database", "notify_port")
        if database_notify_host is None:
            database_notify_host = get_config_str(
                "Database", "notify_hostname")
        elif database_notify_host == "0.0.0.0":
            database_notify_host = "localhost"
        if database_ack_port_num is None:
            database_ack_port_num = get_config_int("Database", "listen_port")

        # build the database socket address used by the notification interface
        database_socket = SocketAddress(
            listen_port=database_ack_port_num,
            notify_host_name=database_notify_host,
            notify_port_no=database_notify_port_num)

        # update socket interface with new demands.
        SpynnakerExternalDevicePluginManager.add_socket_address(
            database_socket)

    @staticmethod
    def activate_live_output_for(
            population, database_notify_host=None,
            database_notify_port_num=None,
            database_ack_port_num=None, board_address=None, port=None,
            host=None, tag=None, strip_sdp=True, use_prefix=False,
            key_prefix=None,
            prefix_type=None, message_type=EIEIOType.KEY_32_BIT,
            right_shift=0, payload_as_time_stamps=True, notify=True,
            use_payload_prefix=True, payload_prefix=None,
            payload_right_shift=0, number_of_packets_sent_per_time_step=0):
        """ Output the spikes from a given population from SpiNNaker as they\
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
        :param str board_address:
            A fixed board address required for the tag, or None if any
            address is OK
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
        """
        # pylint: disable=too-many-arguments, too-many-locals, protected-access
        # get default params if none set
        if port is None:
            port = get_config_int("Recording", "live_spike_port")
        if host is None:
            host = get_config_str("Recording", "live_spike_host")

        # add new edge and vertex if required to SpiNNaker graph
        SpynnakerExternalDevicePluginManager.update_live_packet_gather_tracker(
            population._vertex, "LiveSpikeReceiver", port, host, board_address,
            tag, strip_sdp, use_prefix, key_prefix, prefix_type,
            message_type, right_shift, payload_as_time_stamps,
            use_payload_prefix, payload_prefix, payload_right_shift,
            number_of_packets_sent_per_time_step,
            partition_ids=[SPIKE_PARTITION_ID])

        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def activate_live_output_to(
            population, device, partition_id=SPIKE_PARTITION_ID):
        """ Activate the output of spikes from a population to an external\
            device. Note that all spikes will be sent to the device.

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
    def add_socket_address(socket_address):
        """ Add a socket address to the list to be checked by the\
            notification protocol.

        :param ~spinn_utilities.socket_address.SocketAddress socket_address:
            the socket address
        """
        get_simulator().add_socket_address(socket_address)

    @staticmethod
    def update_live_packet_gather_tracker(
            vertex_to_record_from, lpg_label, port=None, hostname=None,
            board_address=None, tag=None, strip_sdp=True, use_prefix=False,
            key_prefix=None, prefix_type=None,
            message_type=EIEIOType.KEY_32_BIT,
            right_shift=0, payload_as_time_stamps=True,
            use_payload_prefix=True, payload_prefix=None,
            payload_right_shift=0, number_of_packets_sent_per_time_step=0,
            partition_ids=None):
        """ Add an edge from a vertex to the live packet gatherer, builds as\
            needed and has all the parameters for the creation of the live\
            packet gatherer if needed.

        :param vertex_to_record_from:
        :type vertex_to_record_from:
            ~pacman.model.graphs.application.ApplicationVertex or
            ~pacman.model.graphs.machine.MachineVertex
        :param str lpg_label:
        :param int port:
        :param str hostname:
        :param str board_address:
        :param int tag:
        :param bool strip_sdp:
        :param bool use_prefix:
        :param int key_prefix:
        :param ~spinnman.messages.eieio.EIEIOPrefix prefix_type:
        :param ~spinnman.messages.eieio.EIEIOType message_type:
        :param int right_shift:
        :param bool payload_as_time_stamps:
        :param bool use_payload_prefix:
        :param int payload_prefix:
        :param int payload_right_shift:
        :param int number_of_packets_sent_per_time_step:
        :param list(str) partition_ids:
        """
        # pylint: disable=too-many-arguments, too-many-locals
        params = LivePacketGatherParameters(
            port=port, hostname=hostname, tag=tag, board_address=board_address,
            strip_sdp=strip_sdp, use_prefix=use_prefix, key_prefix=key_prefix,
            prefix_type=prefix_type, message_type=message_type,
            right_shift=right_shift, payload_prefix=payload_prefix,
            payload_as_time_stamps=payload_as_time_stamps,
            use_payload_prefix=use_payload_prefix,
            payload_right_shift=payload_right_shift,
            number_of_packets_sent_per_time_step=(
                number_of_packets_sent_per_time_step),
            label=lpg_label)

        # add to the tracker
        get_simulator().add_live_packet_gatherer_parameters(
            params, vertex_to_record_from, partition_ids)

    @staticmethod
    def add_poisson_live_rate_control(
            poisson_population, control_label_extension="_control",
            receive_port=None, database_notify_host=None,
            database_notify_port_num=None,
            database_ack_port_num=None, notify=True,
            reserve_reverse_ip_tag=False):
        """ Add a live rate controller to a Poisson population.

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
        control_label = "{}{}".format(vertex.label, control_label_extension)
        controller = ReverseIpTagMultiCastSource(
            n_keys=vertex.n_atoms, label=control_label,
            receive_port=receive_port,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag)
        SpynnakerExternalDevicePluginManager.add_application_vertex(controller)
        SpynnakerExternalDevicePluginManager.add_edge(
            controller, vertex, LIVE_POISSON_CONTROL_PARTITION_ID)
        if notify:
            SpynnakerExternalDevicePluginManager.add_database_socket_address(
                database_notify_host, database_notify_port_num,
                database_ack_port_num)

    @staticmethod
    def add_edge(vertex, device_vertex, partition_id):
        """ Add an edge between two vertices (often a vertex and a external\
            device) on a given partition.

        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            the pre-vertex to connect the edge from
        :param device_vertex: the post vertex to connect the edge to
        :type device_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str partition_id: the partition identifier for making nets
        """
        _spinnaker = get_simulator()
        edge = ApplicationEdge(vertex, device_vertex)
        _spinnaker.add_application_edge(edge, partition_id)

    @staticmethod
    def add_application_vertex(vertex):
        get_simulator().add_application_vertex(vertex)
