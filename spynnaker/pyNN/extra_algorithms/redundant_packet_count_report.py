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

from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.interface.provenance import (
    ProvenanceReader, ProvenanceWriter)
from spinn_front_end_common.utilities.globals_variables import (
    report_default_directory)
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))

REDUNDANCY_BY_CORE = (
    "CREATE VIEW IF NOT EXISTS redundancy_by_core AS "
    "SELECT pro.x, pro.y, pro.p, source, "
       "received, filtered, invalid, failed, " 
       "filtered + invalid + failed AS redunant, " 
       "filtered + invalid + failed + received AS total, "
       "(filtered + invalid + failed) * 100.0 / " 
          "(filtered + invalid + failed + received) AS percent "
    "FROM" 
        "(SELECT x, y, p, total as received, source "
        "FROM core_stats_view "
        f"WHERE description = \"{PopulationMachineVertex.SPIKES_PROCESSED}\") "
        "AS pro "
    "LEFT JOIN "	
        "(SELECT x, y, p, total AS filtered "
        "FROM core_stats_view "	
        "WHERE description = " 
           f"\"{PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS}\") AS bit "
    "LEFT JOIN "	
        "(SELECT x, y, p, total AS invalid "
        "FROM core_stats_view "	
        "WHERE description = "
            f"\"{PopulationMachineVertex.INVALID_MASTER_POP_HITS}\") AS inv "
    "LEFT JOIN "	
        "(SELECT x, y, p, total AS failed "
        "FROM core_stats_view "	
        "WHERE description = "
            f"\"{PopulationMachineVertex.GHOST_SEARCHES}\") AS fai "
    "WHERE pro.x = bit.x AND pro.y = bit.y AND pro.p = bit.p " 
       "AND pro.x = inv.x AND pro.y = inv.y AND pro.p = inv.p " 
       "AND pro.x = fai.x AND pro.y = fai.y AND pro.p = fai.p")


REDUNDANCY_SUMMARY = (
    "CREATE VIEW IF NOT EXISTS redundancy_summary AS "
    "SELECT SUM(total), MAX(total), MIN(total), AVG(total), "
    "   SUM(redunant), MAX(redunant), MIN(redunant), AVG(redunant), "
    "   MAX(percent), MIN(percent), AVG(percent), "
    "   SUM(redunant) * 100.0 / SUM(total) as global_percent "
    "FROM redundancy_by_core")


class RedundantPacketCountReport(object):

    _FILE_NAME = "redundant_packet_count.rpt"
    _N_PROV_ITEMS_NEEDED = 4
    _MAX = 100

    def __call__(self, provenance_items):
        """

        :param provenance_items: IGNORED ONLY FOR ALGORITHM ORDER
        :type provenance_items: object
        :return:
        """
        file_name = os.path.join(report_default_directory(), self._FILE_NAME)

        self._create_views()
        try:
            with open(file_name, "w") as f:
                self._write_report(f)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Generate_placement_reports: Can't open file"
                             " {} for writing.", self._FILE_NAME)

    def _create_views(self):
        with ProvenanceWriter() as db:
            with db.transaction() as cur:
                cur.execute(REDUNDANCY_BY_CORE)
                cur.execute(REDUNDANCY_SUMMARY)

    def _write_report(self, output):
        reader = ProvenanceReader()
        for data in reader.run_query("select * from redundancy_by_core"):
            (x, y, p, source, received, filtered, invalid, failed,
                redundant, total, percent) = data
            output.write(f"\ncore {source} \n")
            output.write(f"    {total} packets received. \n")
            output.write(f"    {redundant} were detected as "
                         "redundant packets by the bitfield filter. \n")
            output.write(
                f"    {filtered} were detected as having no targets "
                f"after the DMA stage. \n")
            output.write(
                f"    {invalid} were detected as packets which "
                f"we should not have received in the first place. \n")
            output.write(f"    Overall this makes a redundant percentage of "
                         f"{percent}\n")
        data = reader.run_query("select * from redundancy_summary")
        (sum_total, max_total, min_total, avg_total,
            sum_reduant, max_redundant, min_redundant, avg_redundant,
            max_percent, min_percent, avg_percent, global_percent) = data[0]
        output.write(f"\nThe total packets flown in system was "
                     f"{sum_total}\n")
        output.write(f"    The max, min and avergae per core was {max_total}, "
                     f"{min_total}, {avg_total} packets.\n")
        output.write(f"The total redundant packets was "
                     f"{sum_reduant}\n")
        output.write(f"    The max, min and avergae per core was "
                     f"{max_redundant}, {min_redundant}, {avg_redundant} "
                     f"packets.\n")
        output.write(
            f"The percentages of redundant packets was {global_percent}\n")
        output.write(f"    The max and min percentages of redundant "
                     f"packets are {max_percent} and {min_percent}. \n")
        output.write(
            f"    The average redundant percentages from each "
            f"core were {avg_percent} accordingly.\n")


if __name__ == '__main__':
    print(REDUNDANCY_BY_CORE)
    print(REDUNDANCY_SUMMARY)