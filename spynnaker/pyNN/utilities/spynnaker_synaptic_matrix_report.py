import numpy
import logging
import os
from spinn_utilities.progress_bar import ProgressBar

from spynnaker.pyNN import exceptions, ProjectionApplicationEdge

logger = logging.getLogger(__name__)


class SpYNNakerSynapticMatrixReport(object):
    """
    generates the synaptic matrix for reporting purposes
    """

    def __call__(self, report_folder, connection_holder, dsg_targets):
        """ converts synaptic matrix for every application edge.
        """
        if dsg_targets is None:
            raise exceptions.SynapticConfigurationException(
                "dsg targets should not be none, used as a check for "
                "connection holder data to be generated")

        # generate folder for synaptic reports
        top_level_folder = os.path.join(
            report_folder, "synaptic_matrix_reports")
        if not os.path.exists(top_level_folder):
            os.mkdir(top_level_folder)

        # create progress bar
        progress = ProgressBar(connection_holder.keys(),
                               "Generating synaptic matrix reports")

        # Update the print options to display everything
        print_opts = numpy.get_printoptions()
        try:
            numpy.set_printoptions(threshold=numpy.nan)
            # for each application edge, write matrix in new file
            for application_edge, _ in progress.over(connection_holder.keys()):
                # only write matrix's for edges which have matrix's
                if isinstance(application_edge, ProjectionApplicationEdge):
                    self._write_matrix_for_application_edge(
                        top_level_folder, application_edge, connection_holder)
        finally:
            # Reset the print options
            numpy.set_printoptions(**print_opts)

    @staticmethod
    def _write_matrix_for_application_edge(folder, edge, connection_holder):
        # figure new file name
        file_name = os.path.join(
            folder,
            "synaptic_matrix_for_application_edge_{}".format(edge.label))
        try:
            with open(file_name, "w") as output:
                # write all data for all synapse_information's in same file
                for info in edge.synapse_information:
                    output.write("{}".format(connection_holder[(edge, info)]))
        except IOError:
            logger.error("Generate_placement_reports: Can't open file"
                         " {} for writing.".format(file_name))
