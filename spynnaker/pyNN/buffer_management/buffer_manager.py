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
from spynnaker.pyNN.utilities import utility_calls

import struct


class BufferManager(object):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host, transciever):
        self._placements = placements
        self._routing_key_infos = routing_key_infos
        self._graph_mapper = graph_mapper
        self._port = port
        self._local_host = local_host
        self._transciever = transciever
        self._recieve_vertices = dict()
        self._sender_vertices = dict()
        self._sender_thread = BufferSendThread(transciever)
        self._recieve_thread = BufferRecieveThread(transciever)
        self._sender_thread.start()
        self._recieve_thread.start()

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
        :type message: spinnman.messages.eieio.eieio_message.EIEIOMessage
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
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be extracted from them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._recieve_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def add_sender_vertex(self, manageable_vertex):
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be sent to them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._sender_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def contains_sender_vertices(self):
        """ helper method which determines if the buffer manager is currently
        managing verices which require buffers to be sent to them

        :return:
        """
        if len(self._sender_vertices) == 0:
            return False
        return True

    def load_initial_buffers(self):
        """ takes all the sender vertices and loads the initial buffers

        :return:
        """
        progress_bar = ProgressBar(len(self._recieve_vertices),
                                   "on loading buffer dependant vertices")
        for send_vertex_key in self._recieve_vertices.keys():
            sender_vertex = self._sender_vertices[send_vertex_key]
            for region_id in sender_vertex.receiver_buffer_collection.regions_managed:
                self._handle_a_inital_buffer_for_region(region_id, sender_vertex)
            progress_bar.update()
        progress_bar.end()

    def _handle_a_inital_buffer_for_region(self, region_id, sender_vertex):
        """ collects the initial regions buffered data and transmits it to the
        board based chip's memory

        :param region_id: the region id to load a buffer for
        :type region_id: int
        :param sender_vertex: the vertex to load a buffer for
        :type sender_vertex: a instance of partitionedVertex
        :return:
        """
        region_size = \
            sender_vertex.receiver_buffer_collection.get_size_of_region(region_id)
        self._locate_region_address(region_id, sender_vertex)

        #create a buffer packet to emulate core asking for region data
        placement_of_partitioned_vertex = \
            self._placements.get_placement_of_subvertex(sender_vertex)
        buffered_packet = BufferPacket(
            placement_of_partitioned_vertex.x, placement_of_partitioned_vertex.y,
            placement_of_partitioned_vertex.p,
            spinnman_constants.BUFFER_COMMAND_IDS.BUFFER_SEND, region_id,
            region_size, 0)
        #create a buffer request for the right size
        data_request = sender_vertex.receiver_buffer_collection.\
            process_buffer_packet(buffered_packet)
        #write memory to chip
        self._transciever.write_memory(
            data_request.chip_x, data_request.chip_y,
            data_request.address_pointer, data_request.data)

    def _locate_region_address(self, region_id, sender_vertex):
        """ detemrines if the base adress of the region has been set. if the
        address has not been set, it reads the address from the pointer table.
        ONLY PLACE WHERE THIS IS STORED!

        :param region_id: the region to locate the base address of
        :param sender_vertex: the partitionedVertex to which this region links
        :type region_id: int
        :type sender_vertex: instance of PartitionedVertex
        :return: None
        """
        base_address = sender_vertex.\
            receiver_buffer_collection.get_region_base_address_for(region_id)
        if base_address is None:
            placement = \
                self._placements.get_placement_of_subvertex(sender_vertex)
            app_data_base_address = \
                self._transciever.get_cpu_information_from_core(
                    placement.x, placement.y, placement.p).user[0]

            # Get the position of the region in the pointer table
            region_offset_in_pointer_table = utility_calls.\
                get_region_base_address_offset(app_data_base_address, region_id)
            region_offset_to_core_base = str(list(self._transciever.read_memory(
                placement.x, placement.y, region_offset_in_pointer_table, 4))[0])
            base_address = struct.unpack("<I", region_offset_to_core_base)[0]
            sender_vertex.receiver_buffer_collection.\
                set_region_base_address_for(region_id, base_address)
