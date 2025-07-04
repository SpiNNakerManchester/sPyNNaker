# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from contextlib import contextmanager
import logging
import os
from typing import Dict, Iterator, Tuple
import numpy

from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from spynnaker.pyNN.models.neuron import ConnectionHolder

logger = FormatAdapter(logging.getLogger(__name__))
_DIRNAME = "synaptic_matrix_reports"


@contextmanager
def _print_all() -> Iterator[None]:
    """
    Update the numpy print options to display everything.
    """
    print_opts = numpy.get_printoptions()
    numpy.set_printoptions(threshold=sys.maxsize)
    try:
        yield
    finally:
        numpy.set_printoptions(**print_opts)


class SpYNNakerSynapticMatrixReport(object):
    """
    Generate the synaptic matrices for reporting purposes.
    """

    def __call__(self, connection_holder: Dict[Tuple[
            ProjectionApplicationEdge, SynapseInformation], ConnectionHolder]
                 ) -> None:
        """
        Convert synaptic matrix for every application edge.

        :param connection_holder: where the synaptic matrices are stored
            (possibly after retrieval from the machine)
        """
        # generate folder for synaptic reports
        top_level_folder = os.path.join(
            SpynnakerDataView.get_run_dir_path(), _DIRNAME)
        if not os.path.exists(top_level_folder):
            os.mkdir(top_level_folder)
        # create progress bar
        progress = ProgressBar(connection_holder.keys(),
                               "Generating synaptic matrix reports")

        # Update the print options to display everything
        with _print_all():
            # for each application edge, write matrix in new file
            for edge, _ in progress.over(connection_holder.keys()):
                # only write matrix's for edges which have matrix's
                if isinstance(edge, ProjectionApplicationEdge):
                    # figure new file name
                    self._write_file(os.path.join(
                        top_level_folder,
                        f"synaptic_matrix_for_application_edge_{edge.label}"),
                        connection_holder, edge)

    def _write_file(
            self, file_name: str, connection_holder:  Dict[Tuple[
                ProjectionApplicationEdge, SynapseInformation],
                ConnectionHolder],
            edge: ProjectionApplicationEdge) -> None:
        # open writer
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                # write all data for all synapse_information's in same file
                for info in edge.synapse_information:
                    f.write(f"{connection_holder[edge, info]}")
        except IOError:
            logger.exception(
                "Generate_placement_reports: Can't open file {} for writing.",
                file_name)
