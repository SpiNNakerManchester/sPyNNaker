import threading
import os

import logging

logger = logging.getLogger(__name__)


class DataBaseThread(threading.Thread):

    def __init__(self, report_default_directory):
        threading.Thread.__init__(self)
        self._done = False
        self._connection = None
        self._report_default_directory = report_default_directory
        self._callbacks = list()
        self._cur = None
        self.setDaemon(True)

    # noinspection PyPep8
    def run(self):
        import sqlite3 as sqlite
        logger.debug("creating database and initial tables")
        database_address = os.path.join(self._report_default_directory,
                                        "visualiser_database.db")
        self._connection = sqlite.connect(database_address)
        self._cur = self._connection.cursor()
        self._cur.execute("CREATE TABLE Partitionable_vertices("
                          "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "vertex_label TEXT, "
                          "no_atoms INT, "
                          "max_atom_constrant INT)")
        self._cur.execute("CREATE TABLE Partitionable_edges("
                          "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "pre_vertex INTEGER, "
                          "post_vertex INTEGER, "
                          "edge_label TEXT, "
                          "FOREIGN KEY (pre_vertex)"
                              " REFERENCES Partitionable_vertices(vertex_id), "
                          "FOREIGN KEY (post_vertex)"
                              " REFERENCES Partitionable_vertices(vertex_id))")
        self._cur.execute("CREATE TABLE Partitionable_graph("
                          "vertex_id INTEGER, "
                          "edge_id INTEGER, "
                          "FOREIGN KEY (vertex_id) "
                              "REFERENCES Partitionable_vertices(vertex_id), "
                          "FOREIGN KEY (edge_id) "
                              "REFERENCES Partitionable_edges(edge_id), "
                          "PRIMARY KEY (vertex_id, edge_id))")
        self._cur.execute("CREATE TABLE Partitioned_vertices("
                          "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "label TEXT, "
                          "cpu_used INT, "
                          "sdram_used INT, "
                          "dtcm_used INT)")
        self._cur.execute("CREATE TABLE Partitioned_edges("
                          "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "pre_vertex INTEGER, "
                          "post_vertex INTEGER, "
                          "label TEXT, "
                          "FOREIGN KEY (pre_vertex)"
                              " REFERENCES Partitioned_vertices(vertex_id), "
                          "FOREIGN KEY (post_vertex)"
                              " REFERENCES Partitioned_vertices(vertex_id))")
        self._cur.execute("CREATE TABLE Partitioned_graph("
                          "vertex_id INTEGER, "
                          "edge_id INTEGER, "
                          "PRIMARY KEY(vertex_id, edge_id), "
                          "FOREIGN KEY (vertex_id)"
                              " REFERENCES Partitioned_vertices(vertex_id), "
                          "FOREIGN KEY (edge_id)"
                              " REFERENCES Partitioned_edges(edge_id))")
        self._cur.execute("CREATE TABLE graph_mapper_vertex("
                          "partitionable_vertex_id INTEGER, "
                          "partitioned_vertex_id INTEGER, "
                          "lo_atom INT, "
                          "hi_atom INT, "
                          "PRIMARY KEY(partitionable_vertex_id, "
                                      "partitioned_vertex_id), "
                          "FOREIGN KEY (partitioned_vertex_id)"
                              " REFERENCES Partitioned_vertices(vertex_id), "
                          "FOREIGN KEY (partitionable_vertex_id)"
                              " REFERENCES Partitionable_vertices(vertex_id))")
        self._cur.execute("CREATE TABLE graph_mapper_edges("
                          "partitionable_edge_id INTEGER, "
                          "partitioned_edge_id INTEGER, "
                          "PRIMARY KEY(partitionable_edge_id, "
                                      "partitioned_edge_id), "
                          "FOREIGN KEY (partitioned_edge_id)"
                              " REFERENCES Partitioned_edges(edge_id), "
                          "FOREIGN KEY (partitionable_edge_id)"
                              " REFERENCES Partitionable_edges(edge_id))")
        self._cur.execute("CREATE TABLE Placements("
                          "vertex_id INTEGER PRIMARY KEY, "
                          "chip_x INT, "
                          "chip_y INT, "
                          "chip_p INT, "
                          "FOREIGN KEY (vertex_id) "
                              "REFERENCES Partitioned_vertices(vertex_id))")
        self._cur.execute("CREATE TABLE Routing_info("
                          "edge_id INTEGER PRIMARY KEY, "
                          "key INT, "
                          "mask INT, "
                          "FOREIGN KEY (edge_id)"
                              " REFERENCES Partitioned_edges(edge_id))")
        self._cur.execute("CREATE TABLE Routing_table("
                          "chip_x INTEGER, "
                          "chip_y INTEGER, "
                          "position INTEGER, "
                          "key_combo INT, "
                          "mask INT, "
                          "route INT, "
                          "PRIMARY KEY (chip_x, chip_y, position))")

    def add_partitionable_vertices(self, partitionable_graph):
        #add vertices
        for vertex in partitionable_graph.vertices:
            self._cur.execute("INSERT INTO Partitionable_vertices VALUES("
                              "'{}', {}, {})"
                              .format(vertex.label, vertex.n_atoms,
                                      vertex.get_max_atoms_per_core))
        #add edges
        vertices = partitionable_graph.vertices
        for vertex in partitionable_graph.vertices:
            for edge in partitionable_graph.outgoing_edges_from_vertex(vertex):
                self._cur.execute("INSERT INTO Partitionable_edges VALUES("
                                  "{}, {}, '{}');"
                                  .format(vertices.index(edge.pre_vertex) - 1,
                                          vertices.index(edge.post_vertex) - 1,
                                          edge.label))
        #update graph
        edge_id_offset = 0
        for vertex in partitionable_graph.vertices:
            edges = partitionable_graph.outgoing_edges_from_vertex(vertex)
            for edge in partitionable_graph.outgoing_edges_from_vertex(vertex):
                self._cur.execute("INSERT INTO Partitionable_graph VALUES("
                                  "{}, {});"
                                  .format(vertices.index(vertex) - 1,
                                          edges.index(edge) - 1
                                          + edge_id_offset))
            edge_id_offset += len(edges)

    def add_partitioned_vertices(self, partitioned_graph, partitionable_graph,
                                 graph_mapper):
        #add partitioned vertex
        for subvert in partitioned_graph.subvertices:
            self._cur.execute("INSERT INTO Partitioned_vertices VALUES("
                              "'{}', {}, {}, {});"
                              .format(subvert.label,
                                      subvert.resources_required.cpu,
                                      subvert.resources_required.sdram,
                                      subvert.resources_required.dtcm))
        #add mapper for vertices
        subverts = partitioned_graph.subvertices
        vertices = partitionable_graph.vertices
        for subvert in partitioned_graph.subvertices:
            vertex = graph_mapper.get_vertex_from_subvertex(subvert)
            vertex_slice = graph_mapper.get_subvertex_slice(subvert)
            self._cur.execute("INSERT INTO graph_mapper_vertex VALUES("
                              "{}, {}, {}, {});"
                              .format(vertices.index(vertex) - 1,
                                      subverts.index(subvert) - 1,
                                      vertex_slice.lo_atom,
                                      vertex_slice.hi_atom))

        # add partitioned_edges
        for subedge in partitioned_graph.subedges:
            self._cur.execute("INSERT INTO Partitioned_edges VALUES("
                              "{}, {}, '{}');"
                              .format(subverts.index(subedge.pre_subvertex) - 1,
                                      subverts.index(subedge.post_subvertex) - 1,
                                      subedge.label))
        #add graph_mapper edges
        subedges = partitioned_graph.subedges
        edges = partitionable_graph.edges
        for subedge in partitioned_graph.subedges:
            edge = graph_mapper.\
                get_partitionable_edge_from_partitioned_edge(subedge)
            self._cur.execute("INSERT INTO graph_mapper_edges VALUES("
                              "{}, {}".format(edges.index(edge) - 1,
                                              subedges.index(subedge) - 1))

    def add_placements(self, placements):
        raise NotImplementedError

    def add_routing_infos(self, routing_infos):
        raise NotImplementedError

    def add_routing_tables(self, routing_tables):
        raise NotImplementedError

    def create_neuron_to_key_mapping(self, routing_infos, placements,
                                     graph_mapper, partitioned_graph,
                                     partitionable_graph):
        raise NotImplementedError

    def stop(self):
        logger.debug("[data_base_thread] Stopping")
        self._connection.close()
        self._done = True
