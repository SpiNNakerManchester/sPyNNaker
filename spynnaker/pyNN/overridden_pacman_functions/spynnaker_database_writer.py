
from spinn_machine.utilities.progress_bar import ProgressBar
from spinn_front_end_common.utilities import helpful_functions
from spynnaker.pyNN.utilities.database.spynnaker_database_writer import \
    SpynnakerDataBaseWriter


class SpynnakerDatabaseWriter(object):
    """
    """

    def __init__(self):
        self._database_interface = None
        self._user_create_database = None
        self._needs_database = None

    def __call__(
            self, partitioned_graph, user_create_database, tags,
            app_data_runtime_folder, runtime, machine, time_scale_factor,
            machine_time_step, partitionable_graph, graph_mapper, placements,
            routing_infos, router_tables, execute_mapping):

        # add database generation if requested
        self._needs_database = \
            helpful_functions.auto_detect_database(partitioned_graph)
        self._user_create_database = user_create_database
        if ((self._user_create_database == "None" and self._needs_database) or
                self._user_create_database == "True"):

            database_progress = ProgressBar(10, "Creating database")

            self._database_interface = SpynnakerDataBaseWriter(
                app_data_runtime_folder)

            self._database_interface.add_system_params(
                time_scale_factor, machine_time_step, runtime)
            database_progress.update()
            self._database_interface.add_machine_objects(machine)
            database_progress.update()
            self._database_interface.add_partitionable_vertices(
                partitionable_graph)
            database_progress.update()
            self._database_interface.add_partitioned_vertices(
                partitioned_graph, graph_mapper, partitionable_graph)
            database_progress.update()
            self._database_interface.add_placements(placements,
                                                    partitioned_graph)
            database_progress.update()
            self._database_interface.add_routing_infos(
                routing_infos, partitioned_graph)
            database_progress.update()
            self._database_interface.add_routing_tables(router_tables)
            database_progress.update()
            self._database_interface.add_tags(partitioned_graph, tags)
            database_progress.update()
            if execute_mapping:
                self._database_interface.create_atom_to_event_id_mapping(
                    graph_mapper=graph_mapper,
                    partitionable_graph=partitionable_graph,
                    partitioned_graph=partitioned_graph,
                    routing_infos=routing_infos)
            database_progress.update()
            database_progress.update()
            database_progress.end()

        return {"database_interface": self,
                "database_file_path": self.database_file_path}

    @property
    def database_file_path(self):
        """

        :return:
        """
        if ((self._user_create_database == "None" and self._needs_database) or
                self._user_create_database == "True"):
            return self._database_interface.database_path
