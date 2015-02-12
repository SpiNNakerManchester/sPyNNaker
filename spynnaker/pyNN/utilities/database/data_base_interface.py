from spinnman import constants as spinnman_constants
from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spinnman.connections.udp_packet_connections.eieio_command_connection \
    import EieioCommandConnection

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.utilities import constants as spynnaker_constants
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.conf import config

from multiprocessing.pool import ThreadPool
import threading
import os
import logging


logger = logging.getLogger(__name__)


class DataBaseInterface(object):

    def __init__(self, database_directory, wait_for_vis, socket_addresses):
        self._socket_addresses = socket_addresses
        self._done = False
        self._database_directory = database_directory

        # connection to vis stuff
        self._wait_for_vis = wait_for_vis
        self._thread_pool = ThreadPool(processes=1)
        self._wait_pool = ThreadPool(processes=1)
        self._database_address = None

        # set up checks
        self._machine_id = 0
        self._lock_condition = threading.Condition()

        # start creation for database
        self.initilisation()

    def initilisation(self):
        try:
            logger.debug("creating database and initial tables")
            self._database_address = os.path.join(self._database_directory,
                                                  "input_output_database.db")
            self._create_tables()
        except Exception as e:
            print e

    def _create_tables(self):
        import sqlite3 as sqlite
        connection = sqlite.connect(self._database_address)
        cur = connection.cursor()
        cur.execute(
            "CREATE TABLE Machine_layout("
            "machine_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " x_dimension INT, y_dimension INT)")
        cur.execute(
            "CREATE TABLE Machine_chip("
            "no_processors INT, chip_x INTEGER, chip_y INTEGER, "
            "machine_id INTEGER, avilableSDRAM INT, "
            "PRIMARY KEY(chip_x, chip_y, machine_id), "
            "FOREIGN KEY (machine_id) "
            "REFERENCES Machine_layout(machine_id))")
        cur.execute(
            "CREATE TABLE Processor("
            "chip_x INTEGER, chip_y INTEGER, machine_id INTEGER, "
            "avilable_DTCM INT, avilable_CPU INT, physical_id INTEGER, "
            "PRIMARY KEY(chip_x, chip_y, machine_id, physical_id), "
            "FOREIGN KEY (chip_x, chip_y, machine_id) "
            "REFERENCES Machine_chip(chip_x, chip_y, machine_id))")
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
        cur.execute(
            "CREATE TABLE Partitioned_vertices("
            "vertex_id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, "
            "cpu_used INT, sdram_used INT, dtcm_used INT)")
        cur.execute(
            "CREATE TABLE Partitioned_edges("
            "edge_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "pre_vertex INTEGER, post_vertex INTEGER, label TEXT, "
            "FOREIGN KEY (pre_vertex)"
            " REFERENCES Partitioned_vertices(vertex_id), "
            "FOREIGN KEY (post_vertex)"
            " REFERENCES Partitioned_vertices(vertex_id))")
        cur.execute(
            "CREATE TABLE Partitioned_graph("
            "vertex_id INTEGER, edge_id INTEGER, "
            "PRIMARY KEY(vertex_id, edge_id), "
            "FOREIGN KEY (vertex_id)"
            " REFERENCES Partitioned_vertices(vertex_id), "
            "FOREIGN KEY (edge_id)"
            " REFERENCES Partitioned_edges(edge_id))")
        cur.execute(
            "CREATE TABLE graph_mapper_vertex("
            "partitionable_vertex_id INTEGER, "
            "partitioned_vertex_id INTEGER, lo_atom INT, hi_atom INT, "
            "PRIMARY KEY(partitionable_vertex_id, partitioned_vertex_id), "
            "FOREIGN KEY (partitioned_vertex_id)"
            " REFERENCES Partitioned_vertices(vertex_id), "
            "FOREIGN KEY (partitionable_vertex_id)"
            " REFERENCES Partitionable_vertices(vertex_id))")
        cur.execute(
            "CREATE TABLE graph_mapper_edges("
            "partitionable_edge_id INTEGER, partitioned_edge_id INTEGER, "
            "PRIMARY KEY(partitionable_edge_id, partitioned_edge_id), "
            "FOREIGN KEY (partitioned_edge_id)"
            " REFERENCES Partitioned_edges(edge_id), "
            "FOREIGN KEY (partitionable_edge_id)"
            " REFERENCES Partitionable_edges(edge_id))")
        cur.execute(
            "CREATE TABLE Placements("
            "vertex_id INTEGER PRIMARY KEY, machine_id INTEGER, "
            "chip_x INT, chip_y INT, chip_p INT, "
            "FOREIGN KEY (vertex_id) "
            "REFERENCES Partitioned_vertices(vertex_id), "
            "FOREIGN KEY (chip_x, chip_y, chip_p, machine_id) "
            "REFERENCES Processor(chip_x, chip_y, physical_id, "
            "machine_id))")
        cur.execute(
            "CREATE TABLE Routing_info("
            "edge_id INTEGER PRIMARY KEY, key INT, mask INT, "
            "FOREIGN KEY (edge_id) REFERENCES Partitioned_edges(edge_id))")
        cur.execute(
            "CREATE TABLE Routing_table("
            "chip_x INTEGER, chip_y INTEGER, position INTEGER, "
            "key_combo INT, mask INT, route INT, "
            "PRIMARY KEY (chip_x, chip_y, position))")
        cur.execute(
            "CREATE TABLE configuration_parameters("
            "parameter_id TEXT, value REAL, "
            "PRIMARY KEY (parameter_id))")

    # noinspection PyPep8
    def send_visualiser_notifcation(self):
        self._wait_pool.apply_async(self._send_visualiser_notifcation)

    def _send_visualiser_notifcation(self):
        try:
            self._sent_visualisation_confirmation = True
            self._thread_pool.close()
            self._thread_pool.join()

            # after all writing, send notifcation to vis
            if self._wait_for_vis:
                self._notify_visualiser_and_wait()
        except Exception as e:
            print e

    def _notify_visualiser_and_wait(self):

        data_base_message_connections = list()
        for socket_address in self._socket_addresses:
            data_base_message_connection = EieioCommandConnection(
                socket_address.listen_port, socket_address.notify_host_name,
                socket_address.notify_port_no)
            data_base_message_connections.append(data_base_message_connection)

        # create complete message for vis to pick up
        eieio_command_header = EIEIOCommandHeader(
            spinnman_constants.EIEIO_COMMAND_IDS.DATABASE_CONFIRMATION.value)
        eieio_command_message = EIEIOCommandMessage(eieio_command_header)

        # add file path to database into command message.
        # |------P------||------F-----|---------path----------|
        #        0              1               path
        send_file_path = config.getboolean("Database", "send_file_path")
        if send_file_path:
            number_of_chars = len(self._database_address)
            if number_of_chars > spynnaker_constants.MAX_DATABASE_PATH_LENGTH:
                raise exceptions.ConfigurationException(
                    "The file path to the database is too large to be "
                    "transmitted to the visualiser via the command packet, "
                    "please set the file path in your visualiser manually and "
                    "turn off the .cfg parameter [Database] send_file_path "
                    "to False")
            eieio_command_message.add_data(self._database_address)

        # Send command and wait for response
        logger.info("*** Notifying visualiser that the database is ready ***")
        for connection in data_base_message_connections:
            connection.send_eieio_command_message(eieio_command_message)

        for connection in data_base_message_connections:
            connection.receive_eieio_command_message()
        logger.info("*** Confirmation received, continuing ***")

    def wait_for_confirmation(self):
        self._wait_pool.close()
        self._wait_pool.join()

    def add_machine_objects(self, machine):
        self._thread_pool.apply_async(self._add_machine, args=[machine])

    def _add_machine(self, machine):
        try:
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            x_di = machine.max_chip_x + 1
            y_di = machine.max_chip_y + 1
            cur.execute("INSERT INTO Machine_layout("
                        "x_dimension, y_dimension)"
                        " VALUES({}, {})".format(x_di, y_di))
            self._machine_id += 1
            for chip in machine.chips:
                cur.execute(
                    "INSERT INTO Machine_chip("
                    "no_processors, chip_x, chip_y, machine_id) "
                    "VALUES ({}, {}, {}, {})"
                    .format(len(list(chip.processors)), chip.x, chip.y,
                            self._machine_id))
                for processor in chip.processors:
                    cur.execute(
                        "INSERT INTO Processor("
                        "chip_x, chip_y, machine_id, avilable_DTCM, "
                        "avilable_CPU, physical_id)"
                        "VALUES({}, {}, {}, {}, {}, {})"
                        .format(chip.x, chip.y, self._machine_id,
                                processor.dtcm_available,
                                processor.cpu_cycles_available,
                                processor.processor_id))
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def add_partitionable_vertices(self, partitionable_graph):
        self._thread_pool.apply_async(self._add_partitionable_vertices,
                                      args=[partitionable_graph])

    def _add_partitionable_vertices(self, partitionable_graph):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            # add vertices
            for vertex in partitionable_graph.vertices:
                if isinstance(vertex, AbstractRecordableVertex):
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
        except Exception as e:
            print e

    def add_system_params(self, time_scale_factor, machine_time_step, runtime):
        self._thread_pool.apply_async(
            self._add_system_params,
            args=[time_scale_factor, machine_time_step, runtime])

    def _add_system_params(self, time_scale_factor, machine_time_step,
                           runtime):
        try:
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            # Done in 3 statements, as Windows seems to not support
            # multiple value sets in a single statement
            cur.execute(
                "INSERT INTO configuration_parameters (parameter_id, value)"
                " VALUES ('machine_time_step', {})".format(machine_time_step)
            )
            cur.execute(
                "INSERT INTO configuration_parameters (parameter_id, value)"
                " VALUES ('time_scale_factor', {})".format(time_scale_factor)
            )
            cur.execute(
                "INSERT INTO configuration_parameters (parameter_id, value)"
                " VALUES ('runtime', {})".format(runtime)
            )
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def add_partitioned_vertices(self, partitioned_graph, graph_mapper,
                                 partitionable_graph):
        self._thread_pool.apply_async(self._add_partitioned_vertices,
                                      args=[partitioned_graph, graph_mapper,
                                            partitionable_graph])

    def _add_partitioned_vertices(self, partitioned_graph, graph_mapper,
                                  partitionable_graph):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            # add partitioned vertex
            for subvert in partitioned_graph.subvertices:
                cur.execute(
                    "INSERT INTO Partitioned_vertices ("
                    "label, cpu_used, sdram_used, dtcm_used) "
                    "VALUES('{}', {}, {}, {});"
                    .format(subvert.label,
                            subvert.resources_required.cpu.get_value(),
                            subvert.resources_required.sdram.get_value(),
                            subvert.resources_required.dtcm.get_value()))

            # add mapper for vertices
            subverts = list(partitioned_graph.subvertices)
            vertices = partitionable_graph.vertices
            for subvert in partitioned_graph.subvertices:
                vertex = graph_mapper.get_vertex_from_subvertex(subvert)
                vertex_slice = graph_mapper.get_subvertex_slice(subvert)
                cur.execute(
                    "INSERT INTO graph_mapper_vertex ("
                    "partitionable_vertex_id, partitioned_vertex_id, lo_atom, "
                    "hi_atom) "
                    "VALUES({}, {}, {}, {});"
                    .format(vertices.index(vertex) + 1,
                            subverts.index(subvert) + 1,
                            vertex_slice.lo_atom, vertex_slice.hi_atom))

            # add partitioned_edges
            for subedge in partitioned_graph.subedges:
                cur.execute(
                    "INSERT INTO Partitioned_edges ("
                    "pre_vertex, post_vertex, label) "
                    "VALUES({}, {}, '{}');"
                    .format(subverts.index(subedge.pre_subvertex) + 1,
                            subverts.index(subedge.post_subvertex) + 1,
                            subedge.label))

            # add graph_mapper edges
            subedges = list(partitioned_graph.subedges)
            edges = partitionable_graph.edges
            for subedge in partitioned_graph.subedges:
                edge = graph_mapper.\
                    get_partitionable_edge_from_partitioned_edge(subedge)
                cur.execute(
                    "INSERT INTO graph_mapper_edges ("
                    "partitionable_edge_id, partitioned_edge_id) "
                    "VALUES({}, {})"
                    .format(edges.index(edge) + 1,
                            subedges.index(subedge) + 1))

            # add to partitioned graph
            edge_id_offset = 0
            for vertex in partitioned_graph.subvertices:
                edges = partitioned_graph.\
                    outgoing_subedges_from_subvertex(vertex)
                for edge in partitioned_graph.\
                        outgoing_subedges_from_subvertex(vertex):
                    cur.execute(
                        "INSERT INTO Partitioned_graph ("
                        "vertex_id, edge_id)"
                        " VALUES({}, {});"
                        .format(subverts.index(vertex) + 1,
                                subedges.index(edge) + 1 + edge_id_offset))
                edge_id_offset += len(edges)
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def add_placements(self, placements, partitioned_graph):
        self._thread_pool.apply_async(self._add_placements,
                                      args=[placements, partitioned_graph])

    def _add_placements(self, placements, partitioned_graph):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            subverts = list(partitioned_graph.subvertices)
            for placement in placements.placements:
                cur.execute(
                    "INSERT INTO Placements("
                    "vertex_id, chip_x, chip_y, chip_p, machine_id) "
                    "VALUES({}, {}, {}, {}, {})"
                    .format(subverts.index(placement.subvertex) + 1,
                            placement.x, placement.y, placement.p,
                            self._machine_id))
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def add_routing_infos(self, routing_infos, partitioned_graph):
        self._thread_pool.apply_async(self._add_routing_infos,
                                      args=[routing_infos, partitioned_graph])

    def _add_routing_infos(self, routing_infos, partitioned_graph):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            sub_edges = list(partitioned_graph.subedges)
            for routing_info in routing_infos.all_subedge_info:
                cur.execute(
                    "INSERT INTO Routing_info("
                    "edge_id, key, mask) "
                    "VALUES({}, {}, {})"
                    .format(sub_edges.index(routing_info.subedge) + 1,
                            routing_info.key, routing_info.mask))
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def add_routing_tables(self, routing_tables):
        self._thread_pool.apply_async(self._add_routing_tables,
                                      args=[routing_tables])

    def _add_routing_tables(self, routing_tables):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
            cur = connection.cursor()
            for routing_table in routing_tables.routing_tables:
                counter = 0
                for entry in routing_table.multicast_routing_entries:
                    route_entry = 0
                    for processor_id in entry.processor_ids:
                        route_entry |= (1 << (6 + processor_id))
                    for link_id in entry.link_ids:
                        route_entry |= (1 << link_id)
                    cur.execute(
                        "INSERT INTO Routing_table("
                        "chip_x, chip_y, position, key_combo, mask, route) "
                        "VALUES({}, {}, {}, {}, {}, {})"
                        .format(routing_table.x, routing_table.y, counter,
                                entry.key_combo, entry.mask, route_entry))
                    counter += 1
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def create_neuron_to_key_mapping(
            self, partitionable_graph, partitioned_graph, routing_infos,
            graph_mapper, placements):
        self._thread_pool.apply_async(
            self._create_neuron_to_key_mapping,
            args=[partitionable_graph, partitioned_graph, routing_infos,
                  graph_mapper, placements])

    def _create_neuron_to_key_mapping(
            self, partitionable_graph, partitioned_graph, routing_infos,
            graph_mapper, placements):
        try:
            self._lock_condition.acquire()
            import sqlite3 as sqlite
            self._lock_condition.acquire()
            connection = sqlite.connect(self._database_address)
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
                placement = \
                    placements.get_placement_of_subvertex(partitioned_vertex)
                out_going_edges = \
                    partitioned_graph.outgoing_subedges_from_subvertex(
                        partitioned_vertex)
                inserted_keys = list()
                for subedge in out_going_edges:
                    routing_info = routing_infos.\
                        get_subedge_information_from_subedge(subedge)
                    vertex = graph_mapper.\
                        get_vertex_from_subvertex(partitioned_vertex)
                    vertex_id = vertices.index(vertex) + 1
                    vertex_slice = \
                        graph_mapper.get_subvertex_slice(partitioned_vertex)
                    key_to_neuron_map = \
                        routing_info.key_with_atom_ids_function(
                            vertex_slice, vertex, placement, subedge)
                    for neuron_id in key_to_neuron_map.keys():
                        if key_to_neuron_map[neuron_id] not in inserted_keys:
                            cur.execute(
                                "INSERT INTO key_to_neuron_mapping("
                                "vertex_id, key, neuron_id) "
                                "VALUES ({}, {}, {})"
                                .format(vertex_id,
                                        key_to_neuron_map[neuron_id],
                                        neuron_id))
                            inserted_keys.append(key_to_neuron_map[neuron_id])
            connection.commit()
            connection.close()
            self._lock_condition.release()
        except Exception as e:
            print e

    def stop(self):
        logger.debug("[data_base_thread] Stopping")
        self._wait_pool.close()
