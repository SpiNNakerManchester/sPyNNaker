

class BufferManager(object):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host):
        self._placements = placements
        self._routing_key_infos = routing_key_infos
        self._graph_mapper = graph_mapper
        self._port = port
        self._local_host = local_host
        self._recieve_vertices = dict()
        self._sender_vertices = dict()

    @property
    def port(self):
        return self._port

    @property
    def local_host(self):
        return self._local_host

    def receive_buffer_message(self, message):

        #TODO translate the messgae header into a key which can be mapped to a subvertex
        pass

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

