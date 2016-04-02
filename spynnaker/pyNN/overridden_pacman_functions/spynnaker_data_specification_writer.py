from spinn_machine.utilities.progress_bar import ProgressBar

from spinn_front_end_common.interface.interface_functions.\
    front_end_common_partitionable_graph_data_specification_writer \
    import FrontEndCommonPartitionableGraphDataSpecificationWriter
from spinn_front_end_common.utilities.utility_objs.executable_targets \
    import ExecutableTargets

from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex


class SpynnakerDataSpecificationWriter(
        FrontEndCommonPartitionableGraphDataSpecificationWriter):
    """ Executes data specification generation for sPyNNaker
    """

    def __call__(
            self, placements, graph_mapper, tags, executable_finder,
            partitioned_graph, partitionable_graph, routing_infos, hostname,
            report_default_directory, write_text_specs,
            app_data_runtime_folder):

        # Keep the results
        executable_targets = ExecutableTargets()
        dsg_targets = dict()

        # Keep delay extensions until the end
        delay_extension_placements = list()

        # create a progress bar for end users
        progress_bar = ProgressBar(len(list(placements.placements)),
                                   "Generating sPyNNaker data specifications")
        for placement in placements.placements:
            associated_vertex = graph_mapper.get_vertex_from_subvertex(
                placement.subvertex)

            if isinstance(associated_vertex, DelayExtensionVertex):
                delay_extension_placements.append(
                    (placement, associated_vertex))
            else:
                self._generate_data_spec_for_subvertices(
                    placement, associated_vertex, executable_targets,
                    dsg_targets, graph_mapper, tags, executable_finder,
                    partitioned_graph, partitionable_graph, routing_infos,
                    hostname, report_default_directory, write_text_specs,
                    app_data_runtime_folder)
                progress_bar.update()

        for placement, associated_vertex in delay_extension_placements:
            self._generate_data_spec_for_subvertices(
                placement, associated_vertex, executable_targets,
                dsg_targets, graph_mapper, tags, executable_finder,
                partitioned_graph, partitionable_graph, routing_infos,
                hostname, report_default_directory, write_text_specs,
                app_data_runtime_folder)
            progress_bar.update()

        # finish the progress bar
        progress_bar.end()

        return {'executable_targets': executable_targets,
                'dsg_targets': dsg_targets}
