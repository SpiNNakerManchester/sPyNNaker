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
from spinn_front_end_common.interface.provenance import ProvenanceReader
from spinn_front_end_common.utilities.globals_variables import (
    report_default_directory)
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))


class RedundantPacketCountReport(object):

    _FILE_NAME = "redundant_packet_count.rpt"
    _N_PROV_ITEMS_NEEDED = 4
    _MAX = 100

    def __call__(self):
        file_name = os.path.join(report_default_directory(), self._FILE_NAME)

        try:
            with open(file_name, "w") as f:
                self._write_report(f)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Generate_placement_reports: Can't open file"
                             " {} for writing.", self._FILE_NAME)

    def _write_report(self, output):
        output.write(f"Packets report. Totals at the bottom")
        max_incoming = None
        max_percent = None
        reader = ProvenanceReader()
        for (x, y, p, source) in reader.get_cores_with_provenace():
            ghost_searchs = reader.get_provenace_sum_by_core(
                x, y, p, PopulationMachineVertex.GHOST_SEARCHES)
            filtered = reader.get_provenace_sum_by_core(
                x, y, p, PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS)
            invalid = reader.get_provenace_sum_by_core(
                x, y, p, PopulationMachineVertex.INVALID_MASTER_POP_HITS)
            processed = reader.get_provenace_sum_by_core(
                x, y, p, PopulationMachineVertex.SPIKES_PROCESSED)

            try:
                redundant = ghost_searchs + filtered + invalid
                total = redundant + processed
                output.write(f"\ncore {source} \n")
                output.write(f"    {total} packets received. \n")
                output.write(f"    {redundant} were detected as "
                             "redundant packets by the bitfield filter. \n")

                output.write(
                    f"    {filtered} were detected as having no targets "
                    f"after the DMA stage. \n")
                output.write(
                    f"    {ghost_searchs} were detected as packets which "
                    f"we should not have received in the first place. \n")

                if max_incoming is None:
                    max_incoming = total
                    min_incoming = total
                    sum_incoming = total
                    max_redundant = redundant
                    min_redundant = redundant
                    sum_redundant = redundant
                    count = 1
                else:
                    if max_incoming < total:
                        max_incoming = total
                    if min_incoming > total:
                        min_incoming = total
                    sum_incoming += total
                    count += 1
                    if max_redundant < redundant:
                        max_redundant = redundant
                    if min_redundant > redundant:
                        min_redundant = redundant
                    sum_redundant += redundant

            except TypeError:
                total = 0

            if total > 0:
                percent = redundant / total * 100
                output.write(f"    Overall this makes a redundant percentage of "
                             f"{percent}\n")
                if max_percent is None:
                    max_percent = percent
                    min_percent = percent
                    sum_precent = percent
                    count_percent = 1
                else:
                    if max_percent < percent:
                        max_percent = percent
                    if min_percent > percent:
                        min_percent = percent
                    sum_precent += percent
                    count_percent += 1

        if max_incoming is not None:
            output.write(f"\n\noverall, the core with the most incoming "
                         f"packets had {max_incoming} packets.\n")
            output.write(f"    The core with the least incoming packets had "
                         f"{min_incoming} packets.\n")
            output.write(f"    The core with the most redundant packets had "
                         f"{max_redundant} packets.\n")
            output.write(f"    The core with the least redundant packets had "
                         f"{min_redundant} packets.\n")
            output.write(f"    The average incoming and redundant were "
                         f"{sum_incoming/count} and {sum_redundant/count}.\n")

            output.write(f"    The max and min percentages of redundant "
                         f"packets are {max_percent} and {min_percent}. \n")
            output.write(
                f"    The average redundant percentages from each "
                f"core were {sum_precent/count_percent} accordingly.\n")
            output.write(f"    The total packets flown in system was "
                         f"{sum_incoming}\n")
        else:
            output.write("No data to summarise")
