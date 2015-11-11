
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spinn_front_end_common.utilities import helpful_functions
from spynnaker.pyNN.utilities.database.spynnaker_database_writer import \
    SpynnakerDataBaseWriter


class SpynnakerDatabaseWriter(object):
    """
    """

    def __call__(
            self, partitioned_graph, user_create_database, tags,
            wait_on_confirmation, app_data_runtime_folder, runtime, machine,
            database_socket_addresses, time_scale_factor, machine_time_step,
            partitionable_graph, graph_mapper, placements, routing_infos,
            router_tables, execute_mapping):

        database_interface = None
        # add database generation if requested
        needs_database = \
            helpful_functions.auto_detect_database(partitioned_graph)
        if ((user_create_database == "None" and needs_database) or
                user_create_database == "True"):

            database_progress = ProgressBar(10, "Creating database")

            database_interface = SpynnakerDataBaseWriter(
                app_data_runtime_folder, wait_on_confirmation,
                database_socket_addresses)

            database_interface.add_system_params(
                time_scale_factor, machine_time_step, runtime)
            database_progress.update()
            database_interface.add_machine_objects(machine)
            database_progress.update()
            database_interface.add_partitionable_vertices(partitionable_graph)
            database_progress.update()
            database_interface.add_partitioned_vertices(
                partitioned_graph, graph_mapper, partitionable_graph)
            database_progress.update()
            database_interface.add_placements(placements, partitioned_graph)
            database_progress.update()
            database_interface.add_routing_infos(
                routing_infos, partitioned_graph)
            database_progress.update()
            database_interface.add_routing_tables(router_tables)
            database_progress.update()
            database_interface.add_tags(partitioned_graph, tags)
            database_progress.update()
            if execute_mapping:
                database_interface.create_atom_to_event_id_mapping(
                    graph_mapper=graph_mapper,
                    partitionable_graph=partitionable_graph,
                    partitioned_graph=partitioned_graph,
                    routing_infos=routing_infos)
            database_progress.update()
            database_progress.update()
            database_progress.end()
            database_interface.send_read_notification()

        return {"database_interface": database_interface}
