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
from collections import defaultdict

from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))


class RedundantPacketCountReport(object):

    _FILE_NAME = "redundant_packet_count.rpt"

    def __call__(self, provenance_items, report_default_directory):
        file_name = os.path.join(report_default_directory, self._FILE_NAME)

        try:
            with open(file_name, "w") as f:
                self._write_report(f, provenance_items)
        except Exception:
            logger.exception("Generate_placement_reports: Can't open file"
                             " {} for writing.", self._FILE_NAME)

    @staticmethod
    def _write_report(output, provenance_items):
        data = defaultdict(dict)

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
                if len(data[key].keys()) == 4:

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

                    output.write(
                        "core {} \n\n"
                        "    {} packets received.\n"
                        "    {} were detected as redundant packets by the "
                        "bitfield filter.\n"
                        "    {} were detected as having no "
                        "targets after the DMA stage.\n"
                        "    {} were detected as "
                        "packets which we should not have received in the "
                        "first place. \n"
                        "    Overall this makes a redundant "
                        "percentage of {}\n".format(
                            key, total,
                            data[key][
                                PopulationMachineVertex.
                                BIT_FIELD_FILTERED_PACKETS],
                            data[key][PopulationMachineVertex.GHOST_SEARCHES],
                            data[key][
                                PopulationMachineVertex.
                                INVALID_MASTER_POP_HITS],
                            (100.0 / total) * redundant))
