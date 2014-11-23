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
        self._connection.commit()

    def add_partitionable_vertices(self, partitionable_graph):
        #add vertices
        for vertex in partitionable_graph.vertices:
            self._cur.execute("INSERT INTO Partitionable_vertices("
                              "vertex_label, no_atoms, max_atom_constrant)"
                              " VALUES('{}', {}, {});"
                              .format(vertex.label, vertex.n_atoms,
                                      vertex.get_max_atoms_per_core()))
        #add edges
        vertices = partitionable_graph.vertices
        for vertex in partitionable_graph.vertices:
            for edge in partitionable_graph.outgoing_edges_from_vertex(vertex):
                self._cur.execute("INSERT INTO Partitionable_edges ("
                                  "pre_vertex, post_vertex, edge_label) "
                                  "VALUES({}, {}, '{}');"
                                  .format(vertices.index(edge.pre_vertex),
                                          vertices.index(edge.post_vertex),
                                          edge.label))
        #update graph
        edge_id_offset = 0
        for vertex in partitionable_graph.vertices:
            edges = partitionable_graph.outgoing_edges_from_vertex(vertex)
            for edge in partitionable_graph.outgoing_edges_from_vertex(vertex):
                self._cur.execute("INSERT INTO Partitionable_graph ("
                                  "vertex_id, edge_id)"
                                  " VALUES({}, {});"
                                  .format(vertices.index(vertex),
                                          edges.index(edge) + edge_id_offset))
            edge_id_offset += len(edges)
        self._connection.commit()

    def add_partitioned_vertices(self, partitioned_graph, partitionable_graph,
                                 graph_mapper):
        #add partitioned vertex
        for subvert in partitioned_graph.subvertices:
            self._cur.execute("INSERT INTO Partitioned_vertices ("
                              "label, cpu_used, sdram_used, dtcm_used) "
                              "VALUES('{}', {}, {}, {});"
                              .format(subvert.label,
                                      subvert.resources_required.cpu.get_value(),
                                      subvert.resources_required.sdram.get_value(),
                                      subvert.resources_required.dtcm.get_value()))
        #add mapper for vertices
        subverts = list(partitioned_graph.subvertices)
        vertices = partitionable_graph.vertices
        for subvert in partitioned_graph.subvertices:
            vertex = graph_mapper.get_vertex_from_subvertex(subvert)
            vertex_slice = graph_mapper.get_subvertex_slice(subvert)
            self._cur.execute("INSERT INTO graph_mapper_vertex ("
                              "partitionable_vertex_id, partitioned_vertex_id,"
                              "lo_atom, hi_atom) "
                              "VALUES({}, {}, {}, {});"
                              .format(vertices.index(vertex),
                                      subverts.index(subvert),
                                      vertex_slice.lo_atom,
                                      vertex_slice.hi_atom))

        # add partitioned_edges
        for subedge in partitioned_graph.subedges:
            self._cur.execute("INSERT INTO Partitioned_edges ("
                              "pre_vertex, post_vertex, label) "
                              "VALUES({}, {}, '{}');"
                              .format(subverts.index(subedge.pre_subvertex),
                                      subverts.index(subedge.post_subvertex),
                                      subedge.label))
        #add graph_mapper edges
        subedges = list(partitioned_graph.subedges)
        edges = partitionable_graph.edges
        for subedge in partitioned_graph.subedges:
            edge = graph_mapper.\
                get_partitionable_edge_from_partitioned_edge(subedge)
            self._cur.execute("INSERT INTO graph_mapper_edges ("
                              "partitionable_edge_id, partitioned_edge_id) "
                              "VALUES({}, {})"
                              .format(edges.index(edge),
                                      subedges.index(subedge)))

        # add to partitioned graph
        edge_id_offset = 0
        for vertex in partitioned_graph.subvertices:
            edges = partitioned_graph.outgoing_subedges_from_subvertex(vertex)
            for edge in partitioned_graph.outgoing_subedges_from_subvertex(vertex):
                self._cur.execute("INSERT INTO Partitioned_graph ("
                                  "vertex_id, edge_id)"
                                  " VALUES({}, {});"
                                  .format(subverts.index(vertex),
                                          subedges.index(edge) + edge_id_offset))
            edge_id_offset += len(edges)
        self._connection.commit()

    def add_placements(self, placements, partitioned_graph):
        subverts = list(partitioned_graph.subvertices)
        for placement in placements.placements:
            self._cur.execute("INSERT INTO Placements("
                              "vertex_id, chip_x, chip_y, chip_p) "
                              "VALUES({}, {}, {}, {})"
                              .format(subverts.index(placement.subvertex),
                                      placement.x, placement.y, placement.p))
        self._connection.commit()

    def add_routing_infos(self, routing_infos, partitioned_graph):
        sub_edges = list(partitioned_graph.subedges)
        for routing_info in routing_infos.all_subedge_info:
            self._cur.execute("INSERT INTO Routing_info("
                              "edge_id, key, mask) "
                              "VALUES({}, {}, {})"
                              .format(sub_edges.index(routing_info.subedge),
                                      routing_info.key, routing_info.mask))
        self._connection.commit()

    def add_routing_tables(self, routing_tables):
        for routing_table in routing_tables.routing_tables:
            counter = 0
            for entry in routing_table.multicast_routing_entries:
                route_entry = 0
                for processor_id in entry.processor_ids:
                    route_entry |= (1 << (6 + processor_id))
                for link_id in entry.link_ids:
                    route_entry |= (1 << link_id)
                self._cur.execute("INSERT INTO Routing_table("
                                  "chip_x, chip_y, position, key_combo, mask, "
                                  "route) VALUES({}, {}, {}, {}, {}, {})"
                                  .format(routing_table.x, routing_table.y,
                                          counter, entry.key_combo, entry.mask,
                                          route_entry))
                counter += 1
        self._connection.commit()

    def create_neuron_to_key_mapping(self, routing_infos, placements,
                                     graph_mapper, partitioned_graph):
        #create table
        self._cur.execute("CREATE TABLE key_to_neuron_mapping("
                          "vertex_id INTEGER, "
                          "neuron_id INTEGER, "
                          "key INTEGER PRIMARY KEY, "
                          "FOREIGN KEY (vertex_id)"
                              " REFERENCES Partitioned_vertices(vertex_id))")
        #insert into table
        subverts = list(partitioned_graph.subvertices)
        for partitioned_vertex in partitioned_graph.subvertices:
            vertex = graph_mapper.get_vertex_from_subvertex(partitioned_vertex)
            placement = \
                placements.get_placement_of_subvertex(partitioned_vertex)
            out_going_edges = \
                partitioned_graph.outgoing_subedges_from_subvertex(
                    partitioned_vertex)
            for subedge in out_going_edges:
                routing_info = \
                    routing_infos.get_subedge_information_from_subedge(subedge)
                vertex_id = subverts.index(partitioned_vertex)
                vertex_slice = \
                    graph_mapper.get_subvertex_slice(partitioned_vertex)
                key_to_neuron_map = routing_info.key_with_neuron_ids_function(
                    vertex_slice, vertex, placement, subedge)
                for neuron_id in key_to_neuron_map.keys():
                    self._cur.execute("INSERT INTO key_to_neuron_mapping("
                                      "vertex_id, neuron_id, key) "
                                      "VALUES ({}, {}, {})"
                                      .format(vertex_id,
                                              key_to_neuron_map[neuron_id],
                                              neuron_id))
        self._connection.commit()

    def stop(self):
        logger.debug("[data_base_thread] Stopping")
        self._connection.close()
        self._done = True
