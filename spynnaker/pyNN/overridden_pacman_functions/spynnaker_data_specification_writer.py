from spinn_front_end_common.interface.interface_functions import (
    GraphDataSpecificationWriter)
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex


class SpynnakerDataSpecificationWriter(
        GraphDataSpecificationWriter):
    """ Executes data specification generation for sPyNNaker
    """

    __slots__ = ()

    def __call__(
            self, placements, graph, hostname,
            report_default_directory, write_text_specs,
            app_data_runtime_folder, machine, data_n_timesteps,
            graph_mapper=None):
        # pylint: disable=too-many-arguments

        delay_extensions = list()
        placement_order = list()
        for placement in placements.placements:
            associated_vertex = graph_mapper.get_application_vertex(
                placement.vertex)

            if isinstance(associated_vertex, DelayExtensionVertex):
                delay_extensions.append(placement)
            else:
                placement_order.append(placement)
        placement_order.extend(delay_extensions)

        return super(SpynnakerDataSpecificationWriter, self).__call__(
            placements, hostname, report_default_directory, write_text_specs,
            app_data_runtime_folder, machine, data_n_timesteps, graph_mapper,
            placement_order)
