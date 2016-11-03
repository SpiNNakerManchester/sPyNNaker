from spinn_machine.utilities.progress_bar import ProgressBar

from spinn_front_end_common.interface.interface_functions.\
    front_end_common_graph_data_specification_writer import \
    FrontEndCommonGraphDataSpecificationWriter

from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex


class SpynnakerDataSpecificationWriter(
        FrontEndCommonGraphDataSpecificationWriter):
    """ Executes data specification generation for sPyNNaker
    """

    __slots__ = ()

    def __init__(self):
        FrontEndCommonGraphDataSpecificationWriter.__init__(self)

    def __call__(
            self, placements, graph, hostname,
            report_default_directory, write_text_specs,
            app_data_runtime_folder, machine, graph_mapper=None):

        # Keep the results
        dsg_targets = dict()

        # Keep delay extensions until the end
        delay_extension_placements = list()

        # create a progress bar for end users
        progress_bar = ProgressBar(len(list(placements.placements)),
                                   "Generating sPyNNaker data specifications")
        for placement in placements.placements:
            associated_vertex = graph_mapper.get_application_vertex(
                placement.vertex)

            if isinstance(associated_vertex, DelayExtensionVertex):
                delay_extension_placements.append(
                    (placement, associated_vertex))
            else:
                self._generate_data_spec_for_vertices(
                    placement, associated_vertex, dsg_targets, hostname,
                    report_default_directory, write_text_specs,
                    app_data_runtime_folder, machine)
                progress_bar.update()

        for placement, associated_vertex in delay_extension_placements:
            self._generate_data_spec_for_vertices(
                placement, associated_vertex, dsg_targets, hostname,
                report_default_directory, write_text_specs,
                app_data_runtime_folder, machine)
            progress_bar.update()

        # finish the progress bar
        progress_bar.end()

        return dsg_targets
