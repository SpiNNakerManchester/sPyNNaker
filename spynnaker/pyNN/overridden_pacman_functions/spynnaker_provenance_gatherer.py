"""
SpynnakerProvenanceGatherer
"""

# pacman imports
from pacman.interfaces.abstract_provides_provenance_data import \
    AbstractProvidesProvenanceData
from pacman.utilities.utility_objs.progress_bar import ProgressBar

from spinn_front_end_common.utilities import exceptions

# general imports
import os


class SpynnakerProvenanceGatherer(object):
    """
    SpynnakerProvenanceGatherer: generates proenance data specific to the
    spynnaker front end
    """

    def __call__(self, placements, transciever, provenance_file_path, has_ran):

        if has_ran:
            progress = ProgressBar(placements.n_placements,
                                   "Getting provenance data")

            # retrieve provenance data from any cores that provide data
            for placement in placements.placements:
                if isinstance(placement.subvertex,
                              AbstractProvidesProvenanceData):
                    core_file_path = os.path.join(
                        provenance_file_path,
                        "Provanence_data_for_{}_{}_{}_{}.xml".format(
                            placement.subvertex.label,
                            placement.x, placement.y, placement.p))
                    placement.subvertex.write_provenance_data_in_xml(
                        core_file_path, transciever, placement)
                progress.update()
            progress.end()

        else:
            raise exceptions.ConfigurationException(
                "This function has been called before the simulation has ran."
                " This is deemed an error, please rectify and try again")
