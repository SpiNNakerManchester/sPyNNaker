from pacman.utilities.progress_bar import ProgressBar
from spinnman import constants as spinnman_constants
from spinnman import exceptions as spinnman_exceptions
from spinnman.connections.udp_packet_connections.udp_spinnaker_connection import \
    UDPSpinnakerConnection
from spinnman.data.little_endian_byte_array_byte_reader \
    import LittleEndianByteArrayByteReader
from spynnaker.pyNN.buffer_management.buffer_recieve_thread import \
    BufferRecieveThread
from spynnaker.pyNN.buffer_management.buffer_send_thread import BufferSendThread
from spynnaker.pyNN.buffer_management.storage_objects.buffer_packet\
    import BufferPacket


class BufferManager(object):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host, transciever):
        self._placements = placements
        self._routing_key_infos = routing_key_infos
        self._graph_mapper = graph_mapper
        self._port = port
        self._local_host = local_host
        self._recieve_vertices = dict()
        self._sender_vertices = dict()
        self._sort_out_threads(transciever)
        self._sender_thread.start()
        self._recieve_thread.start()

    def _sort_out_threads(self, transciever):
        connections = transciever.get_connections()
        usable_connection = None
        counter = 0
        while usable_connection is None and counter < len(connections):
            if isinstance(connections[counter], UDPSpinnakerConnection):
                usable_connection = connections[counter]
            counter += 1

        if usable_connection is None:
            raise spinnman_exceptions.SpinnmanException(
                "There was no suitable connection avilable to the board."
                "Please recrity and try again")
        #set up connections
        self._sender_thread = BufferSendThread(usable_connection)
        self._recieve_thread = BufferRecieveThread(usable_connection)

    @property
    def port(self):
        return self._port

    @property
    def local_host(self):
        return self._local_host

    def kill_threads(self):
        """ turns off the threads as they are no longer needed

        :return:
        """
        self._recieve_thread.stop()
        self._sender_thread.stop()

    def receive_buffer_message(self, message):
        """ received a eieio message from the port which this manager manages
        and locates what requests are required from it.

        :param message: the message received
        :type spinnman.messages.eieio.eieio_message.EIEIOMessage
        :return:
        """
        if (message.eieio_command_header.command !=
                spinnman_constants.EIEIO_COMMAND_IDS.BUFFER_MANAGEMENT):
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "message.eieio_command_header.command",
                "The command id from this command packet is invalid for "
                "buffer management")

        byte_reader = LittleEndianByteArrayByteReader(message.data)
        buffer_packets = list()
        while not byte_reader.is_at_end():
            buffer_packets.append(
                BufferPacket.
                build_buffer_packet_from_byte_array_reader(byte_reader))

        # check that for each buffer packet request what is needed to be done
        for buffer_packet in buffer_packets:
            key = (buffer_packet.chip_x, buffer_packet.chip_y,
                   buffer_packet.chip_p)

            #if the vertex has recieve requrements, check to see if any are needed
            if (key in self._recieve_vertices.keys() and
                    buffer_packet.command ==
                    spinnman_constants.BUFFER_COMMAND_IDS.BUFFER_RECIEVE):
                receive_data_request = \
                    self._recieve_vertices[key].process_buffer_packet()
                if receive_data_request is not None:
                    self._recieve_thread.add_request(receive_data_request)
            #if the vertex has send requrements, check to see if any are needed
            if (key in self._sender_vertices.keys() and
                    buffer_packet.command ==
                    spinnman_constants.BUFFER_COMMAND_IDS.BUFFER_SEND):
                send_data_request = \
                    self._sender_vertices[key].process_buffer_packet()
                if send_data_request is not None:
                    self._sender_thread.add_request(send_data_request)

    def add_received_vertex(self, manageable_vertex):
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._recieve_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def add_sender_vertex(self, manageable_vertex):
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._sender_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def contains_sender_vertices(self):
        if len(self._sender_vertices) == 0:
            return False
        return True

    def load_initial_buffers(self):
        progress_bar = ProgressBar(len(self._sender_vertices),
                                   "on loading buffer dependant vertices")
        for send_vertex_key in self._sender_vertices.keys():
            sender_vertex = self._sender_vertices[send_vertex_key]
            #TODO complete this part

