import struct
import threading
import time

from pacman.utilities.progress_bar import ProgressBar
from spinnman import exceptions as spinnman_exceptions
from spynnaker.pyNN import exceptions as spynnaker_exceptions
from spinnman.data.little_endian_byte_array_byte_reader \
    import LittleEndianByteArrayByteReader
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.abstract_eieio_packet import \
    AbstractEIEIOPacket
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.create_eieio_packets import \
    create_class_from_reader
from spynnaker.pyNN.buffer_management.buffer_recieve_thread import \
    BufferRecieveThread
from spynnaker.pyNN.buffer_management.buffer_send_thread import BufferSendThread
from spynnaker.pyNN.buffer_management.command_objects.spinnaker_request_buffers import \
    SpinnakerRequestBuffers
from spynnaker.pyNN.buffer_management.command_objects.spinnaker_request_read_data import \
    SpinnakerRequestReadData
from spynnaker.pyNN.buffer_management.command_objects.padding_request import \
    PaddingRequest
from spynnaker.pyNN.utilities import utility_calls


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
        self._thread_lock = threading.Lock()

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

    def receive_buffer_command_message(self, packet):
        """ received a eieio message from the port which this manager manages
        and locates what requests are required from it.

        :param packet: the class related to the message received
        :type packet:
        :return:
        """
        # byte_reader = LittleEndianByteArrayByteReader(message.data)
        # packet = create_class_from_reader(byte_reader)

        with self._thread_lock:
            if isinstance(packet, SpinnakerRequestBuffers):
                key = (packet.x, packet.y, packet.p)
                if key in self._recieve_vertices.keys():
                    print "received packet sequence: {1:d}, space available: {0:d}".format(
                        packet.space_available, packet.sequence_no)
                    data_requests = \
                        self._recieve_vertices[key].get_next_set_of_packets(
                            packet.space_available, packet.region_id,
                            packet.sequence_no)
                    space_used = 0
                    for buffers in data_requests:
                        print "packet to be sent length: {0:d}". format(buffers.length)
                        space_used += buffers.length
                    print "received packet sequence: {3:d}, space available: {0:d}, data requests: {1:d}, total length: {2:d}".format(
                        packet.space_available, len(data_requests), space_used, packet.sequence_no)
                    if len(data_requests) != 0:
                        for buffers in data_requests:
                            data_request = {'data': buffers,
                                            'x': packet.x,
                                            'y': packet.y,
                                            'p': packet.p}
                            self._sender_thread.add_request(data_request)

            elif isinstance(packet, SpinnakerRequestReadData):
                pass
            else:
                raise spinnman_exceptions.SpinnmanInvalidPacketException(
                    packet.__class__,
                    "The command packet is invalid for buffer management")

        # # if (message.eieio_command_header.command !=
        # #         spinnman_constants.EIEIO_COMMAND_IDS.BUFFER_MANAGEMENT):
        # #     raise spinnman_exceptions.SpinnmanInvalidPacketException(
        # #         "message.eieio_command_header.command",
        # #         "The command id from this command packet is invalid for "
        # #         "buffer management")
        #
        # # buffer_packets = list()
        # # while not byte_reader.is_at_end():
        # #     buffer_packets.append(
        # #         BufferPacket.
        # #         build_buffer_packet_from_byte_array_reader(byte_reader))
        #
        # # check that for each buffer packet request what is needed to be done
        # for buffer_packet in buffer_packets:
        #     key = (buffer_packet.chip_x, buffer_packet.chip_y,
        #            buffer_packet.chip_p)
        #
        #     # if the vertex has receive requirements,
        #     # check to see if any are needed
        #     if (key in self._recieve_vertices.keys() and
        #             buffer_packet.command ==
        #             spinnman_constants.RECEIVED_BUFFER_COMMAND_IDS.BUFFER_RECEIVE):
        #         receive_data_requests = \
        #             self._recieve_vertices[key].process_buffered_packet()  # this should modify to get_next_set_of_packets (??)
        #         if len(receive_data_requests) != 0:
        #             for receive_data_request in receive_data_requests:
        #                 self._recieve_thread.add_request(receive_data_request)
        #     # if the vertex has send requirements, check to see if any are
        #     # needed
        #     if (key in self._sender_vertices.keys() and
        #             buffer_packet.command ==
        #             spinnman_constants.RECEIVED_BUFFER_COMMAND_IDS.BUFFER_SEND):
        #         send_data_request = \
        #             self._sender_vertices[key].process_buffered_packet()  # this should modify to get_next_set_of_packets (??)
        #         if send_data_request is not None:
        #             self._sender_thread.add_request(send_data_request)

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
            for region_id in \
                    sender_vertex.receiver_buffer_collection.regions_managed:
                self._handle_a_initial_buffer_for_region(
                    region_id, sender_vertex)
            progress_bar.update()
        progress_bar.end()

    def _handle_a_initial_buffer_for_region(self, region_id, sender_vertex):
        """ collects the initial regions buffered data and transmits it to the
        board based chip's memory

        :param region_id: the region id to load a buffer for
        :type region_id: int
        :param sender_vertex: the vertex to load a buffer for
        :type sender_vertex: a instance of partitionedVertex
        :return:
        """
        region_size = \
            sender_vertex.receiver_buffer_collection.get_size_of_region(
                region_id)

        # create a buffer packet to emulate core asking for region data
        placement_of_partitioned_vertex = \
            self._placements.get_placement_of_subvertex(sender_vertex)

        # buffered_packet = BufferPacket(
        #     placement_of_partitioned_vertex.x,
        #     placement_of_partitioned_vertex.y,
        #     placement_of_partitioned_vertex.p,
        #     spinnman_constants.RECEIVED_BUFFER_COMMAND_IDS.BUFFER_SEND,
        #     region_id, region_size, None)
        # data_requests = sender_vertex.process_buffered_packet(buffered_packet)

        # create a list of buffers to be loaded on the machine, given the region
        # the size and the sequence number
        data_requests = sender_vertex.get_next_set_of_packets(
            region_size, region_id, None)

        # fetch region base address
        self._locate_region_address(region_id, sender_vertex)

        # check if list is empty and if so raise exception
        if len(data_requests) == 0:
            raise spynnaker_exceptions.BufferableRegionTooSmall(
                "buffer region {0:d} in subvertex {1:s} is too small to "
                "contain any type of packet".format(region_id, sender_vertex))
        space_used = 0
        base_address = sender_vertex.receiver_buffer_collection.\
            get_region_base_address_for(region_id)
        # send each data request
        for data_request in data_requests:
            # write memory to chip
            print "writing one packet with length {0:d}".format(data_request.length)
            data_to_be_written = data_request.get_eieio_message_as_byte_array()
            self._transciever.write_memory(
                placement_of_partitioned_vertex.x,
                placement_of_partitioned_vertex.y,
                base_address + space_used, data_to_be_written)

            space_used += len(data_to_be_written)

        # add padding at the end of memory region during initial memory write
        length_to_be_padded = region_size - space_used
        padding_packet = PaddingRequest(length_to_be_padded)
        padding_packet_bytes = padding_packet.get_eieio_message_as_byte_array()
        print "writing padding with length {0:d}".format(len(padding_packet_bytes))
        self._transciever.write_memory(
            placement_of_partitioned_vertex.x,
            placement_of_partitioned_vertex.y,
            base_address + space_used, padding_packet_bytes)

    def _locate_region_address(self, region_id, sender_vertex):
        """ determines if the base address of the region has been set. if the
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
                placement.x, placement.y,
                region_offset_in_pointer_table, 4))[0])
            base_address = struct.unpack("<I", region_offset_to_core_base)[0] + \
                app_data_base_address
            sender_vertex.receiver_buffer_collection.\
                set_region_base_address_for(region_id, base_address)

    # to be copied in the buffered in buffer manager

    @staticmethod
    def create_eieio_messages_from(buffer_data):
        """this method takes a collection of buffers in the form of a single
        byte array and interprets them as eieio messages and returns a list of
        eieio messages

        :param buffer_data: the byte array data
        :type buffer_data: LittleEndianByteArrayByteReader
        :rtype: list of EIEIOMessages
        :return: a list containing EIEIOMessages
        """
        messages = list()
        while not buffer_data.is_at_end():
            eieio_packet = AbstractEIEIOPacket.create_class_from_reader(
                buffer_data)
            messages.append(eieio_packet)
        return messages