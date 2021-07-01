# Copyright (c) 2019-2020 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import logging
import statistics
from collections import defaultdict

from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.utilities.globals_variables import (
    report_default_directory)
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))


class RedundantPacketCountReport(object):

    _FILE_NAME = "redundant_packet_count.rpt"
    _N_PROV_ITEMS_NEEDED = 4
    _MAX = 100

    _CORE_LEVEL_MSG = (
        "core {} \n\n    {} packets received.\n    {} were detected as "
        "redundant packets by the bitfield filter.\n    {} were detected as "
        "having no targets after the DMA stage.\n    {} were detected as "
        "packets which we should not have received in the first place. \n"
        "    Overall this makes a redundant percentage of {}\n")

    _SUMMARY_LEVEL_MSG = (
        "overall, the core with the most incoming packets had {} packets.\n"
        "         The core with the least incoming packets had {} packets.\n"
        "         The core with the most redundant packets had {} packets.\n"
        "         The core with the least redundant packets had {} packets.\n"
        "         The average incoming and redundant were {} and {}.\n"
        "         The max and min percentages of redundant packets are {}"
        " and {}. \n"
        "         The average redundant percentages from each core were {} "
        "accordingly.\n"
        "          The total packets flown in system was {}"
    )

    def __call__(self, provenance_items):
        """
        :param provenance_items:
        :type provenance_items:
            list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """
        file_name = os.path.join(report_default_directory(), self._FILE_NAME)

        try:
            with open(file_name, "w") as f:
                self._write_report(f, provenance_items)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Generate_placement_reports: Can't open file"
                             " {} for writing.", self._FILE_NAME)

    def _write_report(self, output, provenance_items):
        data = defaultdict(dict)

        overall_entries = list()
        overall_redundant = list()
        overall_redundant_percentage = list()

        for provenance_item in provenance_items:
            last_name = provenance_item.names[-1]
            key = provenance_item.names[0]
            if ((last_name == PopulationMachineVertex.GHOST_SEARCHES) or
                    (last_name ==
                        PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS) or
                    (last_name ==
                        PopulationMachineVertex.INVALID_MASTER_POP_HITS) or
                    (last_name == PopulationMachineVertex.SPIKES_PROCESSED)):

                # add to store
                data[key][last_name] = provenance_item.value

                # accum enough data on a core to do summary
                if len(data[key].keys()) == self._N_PROV_ITEMS_NEEDED:

                    # total packets received
                    total = (
                        data[key][PopulationMachineVertex.GHOST_SEARCHES] +
                        data[key][
                            PopulationMachineVertex.
                            BIT_FIELD_FILTERED_PACKETS] +
                        data[key][
                            PopulationMachineVertex.INVALID_MASTER_POP_HITS] +
                        data[key][PopulationMachineVertex.SPIKES_PROCESSED])

                    # total redundant packets
                    redundant = (
                        data[key][PopulationMachineVertex.GHOST_SEARCHES] +
                        data[key][
                            PopulationMachineVertex.
                            BIT_FIELD_FILTERED_PACKETS] +
                        data[key][
                            PopulationMachineVertex.INVALID_MASTER_POP_HITS])

                    percentage = 0
                    if total != 0:
                        percentage = (self._MAX / total) * redundant

                    # add to the trackers for summary data
                    overall_entries.append(total)
                    overall_redundant.append(redundant)
                    overall_redundant_percentage.append(percentage)

                    output.write(self._CORE_LEVEL_MSG.format(
                        key, total,
                        data[key][
                            PopulationMachineVertex.
                            BIT_FIELD_FILTERED_PACKETS],
                        data[key][PopulationMachineVertex.GHOST_SEARCHES],
                        data[key][
                            PopulationMachineVertex.INVALID_MASTER_POP_HITS],
                        percentage))

        # do summary
        if len(overall_entries) != 0:
            output.write(self._SUMMARY_LEVEL_MSG.format(
                max(overall_entries), min(overall_entries),
                max(overall_redundant), min(overall_redundant),
                statistics.mean(overall_entries),
                statistics.mean(overall_redundant),
                max(overall_redundant_percentage),
                min(overall_redundant_percentage),
                statistics.mean(overall_redundant_percentage),
                sum(overall_entries)))
        else:
            output.write("was no data to summarise")
