import logging
import os
from spinn_machine.utilities.progress_bar import ProgressBar

from spynnaker.pyNN import ProjectionApplicationEdge
from spynnaker.pyNN.exceptions import SynapticConfigurationException

logger = logging.getLogger(__name__)


class SpYNNakerSynapticMatrixReport(object):
    """
    generates the synaptic matrix for reporting purposes
    """

    def __call__(self, report_folder, connection_holder, dsg_targets):
        """ converts synaptic matrix for every application edge.
        """

        # Update the print options to display everything
        import numpy
        print_opts = numpy.get_printoptions()
        numpy.set_printoptions(threshold=numpy.nan)

        if dsg_targets is None:
            raise SynapticConfigurationException(
                "dsg targets should not be none, used as a check for "
                "connection holder data to be generated")

        # generate folder for synaptic reports
        top_level_folder = os.path.join(
            report_folder, "synaptic_matrix_reports")
        if not os.path.exists(top_level_folder):
            os.mkdir(top_level_folder)

        # create progress bar
        progress = ProgressBar(
            len(connection_holder.keys()),
            "Generating synaptic matrix reports")

        # for each application edge, write matrix in new file
        for application_edge, _ in connection_holder.keys():

            # only write matrix's for edges which have matrix's
            if isinstance(application_edge, ProjectionApplicationEdge):

                # figure new file name
                file_name = os.path.join(
                    top_level_folder,
                    "synaptic_matrix_for_application_edge_{}"
                    .format(application_edge.label))

                # open writer
                output = None
                try:
                    output = open(file_name, "w")
                except IOError:
                    logger.error("Generate_placement_reports: Can't open file"
                                 " {} for writing.".format(file_name))

                # write all data for all synapse_information's in same file
                for info in application_edge.synapse_information:
                    this_connection_holder = connection_holder[(
                        application_edge, info)]
                    output.write("{}".format(this_connection_holder))
                output.flush()
                output.close()

            progress.update()
        progress.end()

        # Reset the print options
        numpy.set_printoptions(**print_opts)
