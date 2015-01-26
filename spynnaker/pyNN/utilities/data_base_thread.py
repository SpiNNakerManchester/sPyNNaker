from spinnman import constants as spinnman_constants

import threading
import os
import logging
from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.utilities.data_base_message_connection\
    import DataBaseMessageConnection

logger = logging.getLogger(__name__)


class DataBaseThread(threading.Thread):

    def __init__(self, database_directory, execute_mapping,
                 wait_for_vis, listen_port_no=19998,
                 host_to_notify="localhost", port_to_notify=19999):
        threading.Thread.__init__(self)
        self._done = False
        self._connection = None
        self._database_directory = database_directory
        self._execute_mapping = execute_mapping

        # connection to vis stuff
        self._wait_for_vis = wait_for_vis
        self._listen_port = listen_port_no
        self._host_to_notify = host_to_notify
        self._port_to_notify = port_to_notify

        self._cur = None

        # set up lock storage
        self._machine = None
        self._partitionable_graph = None
        self._partitioned_graph = None
        self._graph_mapper = None
        self._placements = None
        self._routing_infos = None
        self._routing_tables = None
        self._complete = False
        self._machine_id = 0
        self._time_scale_factor = None
        self._machine_time_step = None
        self._runtime = None

        # set up checks
        self._done_machine_format = False
        self._done_paritioning = False
        self._done_partitioned = False
        self._done_placements = False
        self._done_routing_info = False
        self._done_routing_tables = False
        self._done_mapping = False
        self._done_machine = False
        self._done_system_params = False
        if self._wait_for_vis:
            self._recieved_confirmation = False
        else:
            self._recieved_confirmation = True
        self._lock_condition = threading.Condition()

        # set daemon
        self.setDaemon(True)

    # noinspection PyPep8
    def run(self):
        try:
            import sqlite3 as sqlite
            logger.debug("creating database and initial tables")
            database_address = os.path.join(self._database_directory,
                                            "visualiser_database.db")
            self._connection = sqlite.connect(database_address)
            self._cur = self._connection.cursor()
            self._cur.execute(
                "CREATE TABLE Machine_layout("
                "machine_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " x_dimension INT, y_dimension INT)")
            self._cur.execute(
                "CREATE TABLE Machine_chip("
                "no_processors INT, chip_x INTEGER, chip_y INTEGER, "
                "machine_id INTEGER, avilableSDRAM INT, "
                "PRIMARY KEY(chip_x, chip_y, machine_id), "
                "FOREIGN KEY (machine_id) "
                "REFERENCES Machine_layout(machine_id))")
            self._cur.execute(
                "CREATE TABLE Processor("
                "chip_x INTEGER, chip_y INTEGER, machine_id INTEGER, "
                "avilable_DTCM INT, avilable_CPU INT, physical_id INTEGER, "
                "PRIMARY KEY(chip_x, chip_y, machine_id, physical_id), "
                "FOREIGN KEY (chip_x, chip_y, machine_id) "
                "REFERENCES Machine_chip(chip_x, chip_y, machine_id))")
            self._cur.execute(
                "CREATE TABLE Partitionable_vertices("
                "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "vertex_label TEXT, no_atoms INT, max_atom_constrant INT,"
                "recorded INT)")
            self._cur.execute(
                "CREATE TABLE Partitionable_edges("
                "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "pre_vertex INTEGER, post_vertex INTEGER, edge_label TEXT, "
                "FOREIGN KEY (pre_vertex)"
                " REFERENCES Partitionable_vertices(vertex_id), "
                "FOREIGN KEY (post_vertex)"
                " REFERENCES Partitionable_vertices(vertex_id))")
            self._cur.execute(
                "CREATE TABLE Partitionable_graph("
                "vertex_id INTEGER, edge_id INTEGER, "
                "FOREIGN KEY (vertex_id) "
                "REFERENCES Partitionable_vertices(vertex_id), "
                "FOREIGN KEY (edge_id) "
                "REFERENCES Partitionable_edges(edge_id), "
                "PRIMARY KEY (vertex_id, edge_id))")
            self._cur.execute(
                "CREATE TABLE Partitioned_vertices("
                "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, "
                "cpu_used INT, sdram_used INT, dtcm_used INT)")
            self._cur.execute(
                "CREATE TABLE Partitioned_edges("
                "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "pre_vertex INTEGER, post_vertex INTEGER, label TEXT, "
                "FOREIGN KEY (pre_vertex)"
                " REFERENCES Partitioned_vertices(vertex_id), "
                "FOREIGN KEY (post_vertex)"
                " REFERENCES Partitioned_vertices(vertex_id))")
            self._cur.execute(
                "CREATE TABLE Partitioned_graph("
                "vertex_id INTEGER, edge_id INTEGER, "
                "PRIMARY KEY(vertex_id, edge_id), "
                "FOREIGN KEY (vertex_id)"
                " REFERENCES Partitioned_vertices(vertex_id), "
                "FOREIGN KEY (edge_id)"
                " REFERENCES Partitioned_edges(edge_id))")
            self._cur.execute(
                "CREATE TABLE graph_mapper_vertex("
                "partitionable_vertex_id INTEGER, "
                "partitioned_vertex_id INTEGER, lo_atom INT, hi_atom INT, "
                "PRIMARY KEY(partitionable_vertex_id, partitioned_vertex_id), "
                "FOREIGN KEY (partitioned_vertex_id)"
                " REFERENCES Partitioned_vertices(vertex_id), "
                "FOREIGN KEY (partitionable_vertex_id)"
                " REFERENCES Partitionable_vertices(vertex_id))")
            self._cur.execute(
                "CREATE TABLE graph_mapper_edges("
                "partitionable_edge_id INTEGER, partitioned_edge_id INTEGER, "
                "PRIMARY KEY(partitionable_edge_id, partitioned_edge_id), "
                "FOREIGN KEY (partitioned_edge_id)"
                " REFERENCES Partitioned_edges(edge_id), "
                "FOREIGN KEY (partitionable_edge_id)"
                " REFERENCES Partitionable_edges(edge_id))")
            self._cur.execute(
                "CREATE TABLE Placements("
                "vertex_id INTEGER PRIMARY KEY, machine_id INTEGER, "
                "chip_x INT, chip_y INT, chip_p INT, "
                "FOREIGN KEY (vertex_id) "
                "REFERENCES Partitioned_vertices(vertex_id), "
                "FOREIGN KEY (chip_x, chip_y, chip_p, machine_id) "
                "REFERENCES Processor(chip_x, chip_y, physical_id, "
                "machine_id))")
            self._cur.execute(
                "CREATE TABLE Routing_info("
                "edge_id INTEGER PRIMARY KEY, key INT, mask INT, "
                "FOREIGN KEY (edge_id) REFERENCES Partitioned_edges(edge_id))")
            self._cur.execute(
                "CREATE TABLE Routing_table("
                "chip_x INTEGER, chip_y INTEGER, position INTEGER, "
                "key_combo INT, mask INT, route INT, "
                "PRIMARY KEY (chip_x, chip_y, position))")
            self._cur.execute(
                "CREATE TABLE configuration_parameters("
                "parameter_id TEXT, value REAL, "
                "PRIMARY KEY (parameter_id))")
        except Exception as e:
            print e
        self._connection.commit()
        while not self._complete:
            self._lock_condition.acquire()
            while ((self._partitionable_graph is None and
                    not self._done_paritioning)
                   or (self._partitioned_graph is None and
                       not self._done_partitioned)
                   or (self._placements is None and not self._done_placements)
                   or (self._routing_infos is None and
                       not self._done_routing_info)
                   or (self._routing_tables is None and
                       not self._done_routing_tables)
                   and not self._complete and self._machine is None):
                self._lock_condition.wait()
            if (self._machine_time_step is not None and
                    self._time_scale_factor is not None and
                    self._runtime is not None
                    and not self._done_system_params):
                self._lock_condition.release()
                self._add_system_params()
            elif self._machine is not None and not self._done_machine:
                self._lock_condition.release()
                self._add_machine()
            elif (self._partitionable_graph is not None and
                    not self._done_paritioning):
                self._lock_condition.release()
                self._add_partitionable_vertices()
                self._done_paritioning = True
            elif (self._partitioned_graph is not None and
                    not self._done_partitioned):
                self._lock_condition.release()
                self._add_partitioned_vertices()
                self._done_partitioned = True
            elif self._placements is not None and not self._done_placements:
                self._lock_condition.release()
                self._add_placements()
                self._done_placements = True
            elif (self._routing_infos is not None and
                    not self._done_routing_info):
                self._lock_condition.release()
                self._add_routing_infos()
                self._done_routing_info = True
            elif (self._routing_tables is not None and
                    not self._done_routing_tables):
                self._lock_condition.release()
                self._add_routing_tables()
                self._done_routing_tables = True
            if (self._partitioned_graph is not None
                    and self._graph_mapper is not None
                    and self._placements is not None and self._execute_mapping
                    and self._routing_infos is not None and
                    not self._done_mapping):
                self._create_neuron_to_key_mapping()
                self._execute_mapping = True
            # check about ending and sending notification
            if (self._done_mapping and self._done_placements and
                    self._done_routing_tables and self._done_partitioned and
                    self._done_routing_info and self._done_system_params and
                    ((self._done_mapping and self._execute_mapping) or
                        not self._execute_mapping)):
                self._complete = True
        if self._wait_for_vis:
            self._notify_visualiser_and_wait()

        self._lock_condition.acquire()
        if not self._done:
            self._lock_condition.wait()
        self._lock_condition.release()
        self._connection.close()

    def _notify_visualiser_and_wait(self):
        data_base_message_connection = DataBaseMessageConnection(
            self._listen_port, self._host_to_notify, self._port_to_notify)

        # create complete message for vis to pick up
        eieio_command_header = EIEIOCommandHeader(
            spinnman_constants.EIEIO_COMMAND_IDS.DATABASE_CONFIRMATION.value)
        eieio_command_message = EIEIOCommandMessage(eieio_command_header,
                                                    bytearray())
        # Send command and wait for response
        logger.info("*** Notifying visualiser that the database is ready ***")
        data_base_message_connection.send_eieio_command_message(
            eieio_command_message)
        data_base_message_connection.receive_eieio_command_message()
        logger.info("*** Confirmation received, continuing ***")
        self._received_confirmation()

    def _received_confirmation(self):
        self._lock_condition.acquire()
        self._recieved_confirmation = True
        self._lock_condition.notify()
        self._lock_condition.release()

    def wait_for_confirmation(self):
        self._lock_condition.acquire()
        while not self._recieved_confirmation:
            self._lock_condition.wait()
        self._lock_condition.release()

    def add_machine_objects(self, machine):
        self._lock_condition.acquire()
        self._machine = machine
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_machine(self):
        x_di = self._machine.max_chip_x + 1
        y_di = self._machine.max_chip_y + 1
        self._cur.execute("INSERT INTO Machine_layout("
                          "x_dimension, y_dimension)"
                          " VALUES({}, {})".format(x_di, y_di))
        self._machine_id += 1
        for chip in self._machine.chips:
            self._cur.execute(
                "INSERT INTO Machine_chip("
                "no_processors, chip_x, chip_y, machine_id) "
                "VALUES ({}, {}, {}, {})"
                .format(len(list(chip.processors)), chip.x, chip.y,
                        self._machine_id))
            for processor in chip.processors:
                self._cur.execute(
                    "INSERT INTO Processor("
                    "chip_x, chip_y, machine_id, avilable_DTCM, avilable_CPU, "
                    "physical_id)"
                    "VALUES({}, {}, {}, {}, {}, {})"
                    .format(chip.x, chip.y, self._machine_id,
                            processor.dtcm_available,
                            processor.cpu_cycles_available,
                            processor.processor_id))
        self._connection.commit()
        self._done_machine = True

    def add_partitionable_vertices(self, partitionable_graph):
        self._lock_condition.acquire()
        self._partitionable_graph = partitionable_graph
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_system_params(self):

        # Done in 3 statements, as Windows seems to not support multiple value
        # sets in a single statement
        self._cur.execute(
            "INSERT INTO configuration_parameters (parameter_id, value)"
            " VALUES ('machine_time_step', {})".format(self._machine_time_step)
        )
        self._cur.execute(
            "INSERT INTO configuration_parameters (parameter_id, value)"
            " VALUES ('time_scale_factor', {})".format(self._time_scale_factor)
        )
        self._cur.execute(
            "INSERT INTO configuration_parameters (parameter_id, value)"
            " VALUES ('runtime', {})".format(self._runtime)
        )
        self._done_system_params = True
        self._connection.commit()

    def add_system_params(self, time_scale_factor, machine_time_step, runtime):
        self._lock_condition.acquire()
        self._time_scale_factor = time_scale_factor
        self._machine_time_step = machine_time_step
        self._runtime = runtime
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_partitionable_vertices(self):
        # add vertices
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractRecordableVertex):
                self._cur.execute(
                    "INSERT INTO Partitionable_vertices("
                    "vertex_label, no_atoms, max_atom_constrant, recorded)"
                    " VALUES('{}', {}, {}, {});"
                    .format(vertex.label, vertex.n_atoms,
                            vertex.get_max_atoms_per_core(),
                            int(vertex.record)))
            else:
                self._cur.execute(
                    "INSERT INTO Partitionable_vertices("
                    "vertex_label, no_atoms, max_atom_constrant, recorded)"
                    " VALUES('{}', {}, {}, 0);"
                    .format(vertex.label, vertex.n_atoms,
                            vertex.get_max_atoms_per_core()))
        # add edges
        vertices = self._partitionable_graph.vertices
        for vertex in self._partitionable_graph.vertices:
            for edge in self._partitionable_graph.\
                    outgoing_edges_from_vertex(vertex):
                self._cur.execute(
                    "INSERT INTO Partitionable_edges ("
                    "pre_vertex, post_vertex, edge_label) "
                    "VALUES({}, {}, '{}');"
                    .format(vertices.index(edge.pre_vertex) + 1,
                            vertices.index(edge.post_vertex) + 1, edge.label))
        # update graph
        edge_id_offset = 0
        for vertex in self._partitionable_graph.vertices:
            edges = self._partitionable_graph.outgoing_edges_from_vertex(
                vertex)
            for edge in self._partitionable_graph.\
                    outgoing_edges_from_vertex(vertex):
                self._cur.execute(
                    "INSERT INTO Partitionable_graph ("
                    "vertex_id, edge_id)"
                    " VALUES({}, {})"
                    .format(vertices.index(vertex) + 1,
                            edges.index(edge) + edge_id_offset))
            edge_id_offset += len(edges)
        self._connection.commit()

    def add_partitioned_vertices(self, partitioned_graph, graph_mapper):
        self._lock_condition.acquire()
        self._partitioned_graph = partitioned_graph
        self._graph_mapper = graph_mapper
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_partitioned_vertices(self):

        # add partitioned vertex
        for subvert in self._partitioned_graph.subvertices:
            self._cur.execute(
                "INSERT INTO Partitioned_vertices ("
                "label, cpu_used, sdram_used, dtcm_used) "
                "VALUES('{}', {}, {}, {});"
                .format(subvert.label,
                        subvert.resources_required.cpu.get_value(),
                        subvert.resources_required.sdram.get_value(),
                        subvert.resources_required.dtcm.get_value()))

        # add mapper for vertices
        subverts = list(self._partitioned_graph.subvertices)
        vertices = self._partitionable_graph.vertices
        for subvert in self._partitioned_graph.subvertices:
            vertex = self._graph_mapper.get_vertex_from_subvertex(subvert)
            vertex_slice = self._graph_mapper.get_subvertex_slice(subvert)
            self._cur.execute(
                "INSERT INTO graph_mapper_vertex ("
                "partitionable_vertex_id, partitioned_vertex_id, lo_atom, "
                "hi_atom) "
                "VALUES({}, {}, {}, {});"
                .format(vertices.index(vertex) + 1,
                        subverts.index(subvert) + 1,
                        vertex_slice.lo_atom, vertex_slice.hi_atom))

        # add partitioned_edges
        for subedge in self._partitioned_graph.subedges:
            self._cur.execute(
                "INSERT INTO Partitioned_edges ("
                "pre_vertex, post_vertex, label) "
                "VALUES({}, {}, '{}');"
                .format(subverts.index(subedge.pre_subvertex) + 1,
                        subverts.index(subedge.post_subvertex) + 1,
                        subedge.label))

        # add graph_mapper edges
        subedges = list(self._partitioned_graph.subedges)
        edges = self._partitionable_graph.edges
        for subedge in self._partitioned_graph.subedges:
            edge = self._graph_mapper.\
                get_partitionable_edge_from_partitioned_edge(subedge)
            self._cur.execute(
                "INSERT INTO graph_mapper_edges ("
                "partitionable_edge_id, partitioned_edge_id) "
                "VALUES({}, {})"
                .format(edges.index(edge) + 1, subedges.index(subedge) + 1))

        # add to partitioned graph
        edge_id_offset = 0
        for vertex in self._partitioned_graph.subvertices:
            edges = self._partitioned_graph.\
                outgoing_subedges_from_subvertex(vertex)
            for edge in self._partitioned_graph.\
                    outgoing_subedges_from_subvertex(vertex):
                self._cur.execute(
                    "INSERT INTO Partitioned_graph ("
                    "vertex_id, edge_id)"
                    " VALUES({}, {});"
                    .format(subverts.index(vertex) + 1,
                            subedges.index(edge) + 1 + edge_id_offset))
            edge_id_offset += len(edges)
        self._connection.commit()

    def add_placements(self, placements):
        self._lock_condition.acquire()
        self._placements = placements
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_placements(self):
        subverts = list(self._partitioned_graph.subvertices)
        for placement in self._placements.placements:
            self._cur.execute(
                "INSERT INTO Placements("
                "vertex_id, chip_x, chip_y, chip_p, machine_id) "
                "VALUES({}, {}, {}, {}, {})"
                .format(subverts.index(placement.subvertex) + 1, placement.x,
                        placement.y, placement.p, self._machine_id))
        self._connection.commit()

    def add_routing_infos(self, routing_infos):
        self._lock_condition.acquire()
        self._routing_infos = routing_infos
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_routing_infos(self):
        sub_edges = list(self._partitioned_graph.subedges)
        for routing_info in self._routing_infos.all_subedge_info:
            self._cur.execute(
                "INSERT INTO Routing_info("
                "edge_id, key, mask) "
                "VALUES({}, {}, {})"
                .format(sub_edges.index(routing_info.subedge) + 1,
                        routing_info.key, routing_info.mask))
        self._connection.commit()

    def add_routing_tables(self, routing_tables):
        self._lock_condition.acquire()
        self._routing_tables = routing_tables
        self._lock_condition.notify()
        self._lock_condition.release()

    def _add_routing_tables(self):
        for routing_table in self._routing_tables.routing_tables:
            counter = 0
            for entry in routing_table.multicast_routing_entries:
                route_entry = 0
                for processor_id in entry.processor_ids:
                    route_entry |= (1 << (6 + processor_id))
                for link_id in entry.link_ids:
                    route_entry |= (1 << link_id)
                self._cur.execute(
                    "INSERT INTO Routing_table("
                    "chip_x, chip_y, position, key_combo, mask, route) "
                    "VALUES({}, {}, {}, {}, {}, {})"
                    .format(routing_table.x, routing_table.y, counter,
                            entry.key_combo, entry.mask, route_entry))
                counter += 1
        self._connection.commit()

    def _create_neuron_to_key_mapping(self):

        # create table
        self._done_mapping = True
        self._cur.execute(
            "CREATE TABLE key_to_neuron_mapping("
            "vertex_id INTEGER, neuron_id INTEGER, key INTEGER PRIMARY KEY, "
            "FOREIGN KEY (vertex_id)"
            " REFERENCES Partitioned_vertices(vertex_id))")

        # insert into table
        vertices = list(self._partitionable_graph.vertices)
        for partitioned_vertex in self._partitioned_graph.subvertices:
            vertex = self._graph_mapper.get_vertex_from_subvertex(
                partitioned_vertex)
            placement = self._placements.get_placement_of_subvertex(
                partitioned_vertex)
            out_going_edges = \
                self._partitioned_graph.outgoing_subedges_from_subvertex(
                    partitioned_vertex)
            inserted_keys = list()
            for subedge in out_going_edges:
                routing_info = self._routing_infos.\
                    get_subedge_information_from_subedge(subedge)
                vertex = self._graph_mapper.get_vertex_from_subvertex(
                    partitioned_vertex)
                vertex_id = vertices.index(vertex) + 1
                vertex_slice = \
                    self._graph_mapper.get_subvertex_slice(partitioned_vertex)
                key_to_neuron_map = routing_info.key_with_atom_ids_function(
                    vertex_slice, vertex, placement, subedge)
                for neuron_id in key_to_neuron_map.keys():
                    if key_to_neuron_map[neuron_id] not in inserted_keys:
                        self._cur.execute(
                            "INSERT INTO key_to_neuron_mapping("
                            "vertex_id, key, neuron_id) "
                            "VALUES ({}, {}, {})"
                            .format(vertex_id, key_to_neuron_map[neuron_id],
                                    neuron_id))
                        inserted_keys.append(key_to_neuron_map[neuron_id])
        self._connection.commit()

    def stop(self):
        logger.debug("[data_base_thread] Stopping")
        self._lock_condition.acquire()
        self._done = True
        self._lock_condition.notify()
        self._lock_condition.release()
