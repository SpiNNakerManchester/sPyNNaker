"""
SpynnakerDataBaseInterface
"""
# front end common imports
from spinn_front_end_common.utilities.database.\
    data_base_writer import DatabaseWriter

# general imports
import logging
import traceback
from spynnaker.pyNN.models.abstract_models.\
    abstract_population_recordable_vertex import \
    AbstractPopulationRecordableVertex


logger = logging.getLogger(__name__)


class SpynnakerDataBaseInterface(DatabaseWriter):
    """
    SpynnakerDataBaseInterface: the interface for the database system for the
    spynnaker front end
    """

    def __init__(self, database_directory, wait_for_read_confirmation,
                 socket_addresses):
        DatabaseWriter.__init__(
            self, database_directory, wait_for_read_confirmation,
            socket_addresses)

    def add_partitionable_vertices(self, partitionable_graph):
        """

        :param partitionable_graph:
        :return:
        """
        self._thread_pool.apply_async(self._add_partitionable_vertices,
                                      args=[partitionable_graph])

    def _add_partitionable_vertices(self, partitionable_graph):
        # noinspection PyBroadException
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_path)
            cur = connection.cursor()
            cur.execute(
                "CREATE TABLE Partitionable_vertices("
                "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "vertex_label TEXT, no_atoms INT, max_atom_constrant INT,"
                "recorded INT)")
            cur.execute(
                "CREATE TABLE Partitionable_edges("
                "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "pre_vertex INTEGER, post_vertex INTEGER, edge_label TEXT, "
                "FOREIGN KEY (pre_vertex)"
                " REFERENCES Partitionable_vertices(vertex_id), "
                "FOREIGN KEY (post_vertex)"
                " REFERENCES Partitionable_vertices(vertex_id))")
            cur.execute(
                "CREATE TABLE Partitionable_graph("
                "vertex_id INTEGER, edge_id INTEGER, "
                "FOREIGN KEY (vertex_id) "
                "REFERENCES Partitionable_vertices(vertex_id), "
                "FOREIGN KEY (edge_id) "
                "REFERENCES Partitionable_edges(edge_id), "
                "PRIMARY KEY (vertex_id, edge_id))")
            # add vertices
            for vertex in partitionable_graph.vertices:
                if isinstance(vertex, AbstractPopulationRecordableVertex):
                    cur.execute(
                        "INSERT INTO Partitionable_vertices("
                        "vertex_label, no_atoms, max_atom_constrant, recorded)"
                        " VALUES('{}', {}, {}, {});"
                        .format(vertex.label, vertex.n_atoms,
                                vertex.get_max_atoms_per_core(),
                                int(vertex.record)))
                else:
                    cur.execute(
                        "INSERT INTO Partitionable_vertices("
                        "vertex_label, no_atoms, max_atom_constrant, recorded)"
                        " VALUES('{}', {}, {}, 0);"
                        .format(vertex.label, vertex.n_atoms,
                                vertex.get_max_atoms_per_core()))
            # add edges
            vertices = partitionable_graph.vertices
            for vertex in partitionable_graph.vertices:
                for edge in partitionable_graph.\
                        outgoing_edges_from_vertex(vertex):
                    cur.execute(
                        "INSERT INTO Partitionable_edges ("
                        "pre_vertex, post_vertex, edge_label) "
                        "VALUES({}, {}, '{}');"
                        .format(vertices.index(edge.pre_vertex) + 1,
                                vertices.index(edge.post_vertex) + 1,
                                edge.label))
            # update graph
            edge_id_offset = 0
            for vertex in partitionable_graph.vertices:
                edges = partitionable_graph.outgoing_edges_from_vertex(vertex)
                for edge in partitionable_graph.\
                        outgoing_edges_from_vertex(vertex):
                    cur.execute(
                        "INSERT INTO Partitionable_graph ("
                        "vertex_id, edge_id)"
                        " VALUES({}, {})"
                        .format(vertices.index(vertex) + 1,
                                edges.index(edge) + edge_id_offset))
                edge_id_offset += len(edges)
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception:
            traceback.print_exc()

    def create_neuron_to_key_mapping(
            self, partitionable_graph, partitioned_graph, routing_infos,
            graph_mapper):
        """

        :param partitionable_graph:
        :param partitioned_graph:
        :param routing_infos:
        :param graph_mapper:
        :return:
        """
        self._thread_pool.apply_async(
            self._create_neuron_to_key_mapping,
            args=[partitionable_graph, partitioned_graph, routing_infos,
                  graph_mapper])

    def _create_neuron_to_key_mapping(
            self, partitionable_graph, partitioned_graph, routing_infos,
            graph_mapper):
        # noinspection PyBroadException
        try:
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_path)
            cur = connection.cursor()
            # create table
            self._done_mapping = True
            cur.execute(
                "CREATE TABLE key_to_neuron_mapping("
                "vertex_id INTEGER, neuron_id INTEGER, "
                "key INTEGER PRIMARY KEY, "
                "FOREIGN KEY (vertex_id)"
                " REFERENCES Partitioned_vertices(vertex_id))")

            # insert into table
            vertices = list(partitionable_graph.vertices)
            for partitioned_vertex in partitioned_graph.subvertices:
                out_going_edges = (partitioned_graph
                                   .outgoing_subedges_from_subvertex(
                                       partitioned_vertex))
                if len(out_going_edges) > 0:
                    routing_info = (routing_infos
                                    .get_subedge_information_from_subedge(
                                        out_going_edges[0]))
                    vertex = graph_mapper.get_vertex_from_subvertex(
                        partitioned_vertex)
                    vertex_id = vertices.index(vertex) + 1
                    vertex_slice = graph_mapper.get_subvertex_slice(
                        partitioned_vertex)
                    keys = routing_info.get_keys(vertex_slice.n_atoms)
                    neuron_id = vertex_slice.lo_atom
                    for key in keys:
                        cur.execute(
                            "INSERT INTO key_to_neuron_mapping("
                            "vertex_id, key, neuron_id) "
                            "VALUES ({}, {}, {})"
                            .format(vertex_id, key, neuron_id))
                        neuron_id += 1
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception:
            traceback.print_exc()
