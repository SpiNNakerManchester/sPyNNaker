import logging
import numpy
import os
from spinn_utilities.progress_bar import ProgressBar

from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge

logger = logging.getLogger(__name__)
_DIRNAME = "synaptic_matrix_reports"
_TMPL_FILENAME = "synaptic_matrix_for_application_edge_{}"


class SpYNNakerSynapticMatrixReport(object):
    """ Generate the synaptic matrix for reporting purposes
    """

    def __call__(self, report_folder, connection_holder, dsg_targets):
        """ Convert synaptic matrix for every application edge.
        """

        # Update the print options to display everything
        print_opts = numpy.get_printoptions()
        numpy.set_printoptions(threshold=numpy.nan)

        if dsg_targets is None:
            raise SynapticConfigurationException(
                "dsg_targets should not be none, used as a check for "
                "connection holder data to be generated")

        # generate folder for synaptic reports
        top_level_folder = os.path.join(report_folder, _DIRNAME)
        if not os.path.exists(top_level_folder):
            os.mkdir(top_level_folder)

        # create progress bar
        progress = ProgressBar(connection_holder.keys(),
                               "Generating synaptic matrix reports")

        # for each application edge, write matrix in new file
        for edge, _ in progress.over(connection_holder.keys()):
            # only write matrix's for edges which have matrix's
            if isinstance(edge, ProjectionApplicationEdge):
                # figure new file name
                file_name = os.path.join(
                    top_level_folder, _TMPL_FILENAME.format(edge.label))
                self._write_file(file_name, connection_holder, edge)

        # Reset the print options
        numpy.set_printoptions(**print_opts)

    def _write_file(self, file_name, connection_holder, edge):
        # open writer
        try:
            with open(file_name, "w") as f:
                # write all data for all synapse_information's in same file
                for info in edge.synapse_information:
                    f.write("{}".format(connection_holder[edge, info]))
        except IOError:
            logger.exception("Generate_placement_reports: Can't open file"
                             " %s for writing.", file_name)
