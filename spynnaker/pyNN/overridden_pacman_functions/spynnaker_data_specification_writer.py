from spinn_utilities.progress_bar import ProgressBar

from spinn_front_end_common.interface.interface_functions import \
    GraphDataSpecificationWriter

from spynnaker.pyNN.models.utility_models import DelayExtensionVertex


class SpynnakerDataSpecificationWriter(
        GraphDataSpecificationWriter):
    """ Executes data specification generation for sPyNNaker
    """

    __slots__ = ()

    def __init__(self):
        GraphDataSpecificationWriter.__init__(self)

    def __call__(
            self, placements, graph, hostname,
            report_default_directory, write_text_specs,
            app_data_runtime_folder, machine, graph_mapper=None):
        # pylint: disable=too-many-arguments

        # Keep the results
        dsg_targets = dict()

        # Keep delay extensions until the end
        delay_extension_placements = list()

        plist = list(placements.placements)

        # create a progress bar for end users
        progress = ProgressBar(
            plist, "Generating sPyNNaker data specifications")

        for placement in plist:
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
                progress.update()

        for placement, associated_vertex in progress.over(
                delay_extension_placements):
            self._generate_data_spec_for_vertices(
                placement, associated_vertex, dsg_targets, hostname,
                report_default_directory, write_text_specs,
                app_data_runtime_folder, machine)

        return dsg_targets
