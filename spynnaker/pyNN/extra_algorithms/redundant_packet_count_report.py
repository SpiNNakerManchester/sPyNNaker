# Copyright (c) 2019 The University of Manchester
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
import os
import logging
from typing import Final, TextIO, Tuple, cast
from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.interface.provenance import (
    ProvenanceReader, ProvenanceWriter)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))

#: How to make the redundancy information table in the provenance DB
REDUNDANCY_BY_CORE: Final = f"""
    CREATE VIEW IF NOT EXISTS redundancy_by_core AS
    SELECT pro.x, pro.y, pro.p, core_name,
        received, filtered, invalid, failed,
        filtered + invalid + failed AS redundant,
        filtered + invalid + failed + received AS total,
        (filtered + invalid + failed) * 100.0 /
            (filtered + invalid + failed + received) AS percent
    FROM
        (SELECT x, y, p, total as received, core_name
            FROM core_stats_view
            WHERE description = '{PopulationMachineVertex.SPIKES_PROCESSED}')
        AS pro
    LEFT JOIN
        (SELECT x, y, p, total AS filtered
            FROM core_stats_view
            WHERE description =
                '{PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS}')
        AS bit
    LEFT JOIN
       (SELECT x, y, p, total AS invalid
           FROM core_stats_view
           WHERE description =
               '{PopulationMachineVertex.INVALID_MASTER_POP_HITS}')
        AS inv
    LEFT JOIN
        (SELECT x, y, p, total AS failed
            FROM core_stats_view
            WHERE description = '{PopulationMachineVertex.GHOST_SEARCHES}')
        AS fai
    WHERE pro.x = bit.x AND pro.y = bit.y AND pro.p = bit.p
        AND pro.x = inv.x AND pro.y = inv.y AND pro.p = inv.p
        AND pro.x = fai.x AND pro.y = fai.y AND pro.p = fai.p
    """


#: How to generate summary information from the redundancy table
REDUNDANCY_SUMMARY: Final = """
    CREATE VIEW IF NOT EXISTS redundancy_summary AS
    SELECT SUM(total), MAX(total), MIN(total), AVG(total),
        SUM(redundant), MAX(redundant), MIN(redundant), AVG(redundant),
        MAX(percent), MIN(percent), AVG(percent),
        SUM(redundant) * 100.0 / SUM(total) as global_percent
    FROM redundancy_by_core
    """


_FILE_NAME = "redundant_packet_count.rpt"
_N_PROV_ITEMS_NEEDED = 4
_MAX = 100


def redundant_packet_count_report() -> None:
    file_name = os.path.join(SpynnakerDataView.get_run_dir_path(), _FILE_NAME)

    try:
        _create_views()
        with open(file_name, "w", encoding="utf-8") as f:
            _write_report(f)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(
            "Error {} doing redundant_packet_count_report {}:", e, file_name)


def _create_views() -> None:
    with ProvenanceWriter() as db:
        db.execute(REDUNDANCY_BY_CORE)
        db.execute(REDUNDANCY_SUMMARY)


def _write_report(output: TextIO):
    with ProvenanceReader() as db:
        for data in db.run_query("SELECT * FROM redundancy_by_core"):
            (_, _, _, source, _, filtered, invalid, _, redundant, total,
             percent) = cast(Tuple[int, ...], data)
            output.write(f"\ncore {source} \n")
            output.write(f"    {total} packets received.\n")
            output.write(
                f"    {redundant} were detected as redundant packets by the "
                "bitfield filter.\n")
            output.write(
                f"    {filtered} were detected as having no targets "
                "after the DMA stage.\n")
            output.write(
                f"    {invalid} were detected as packets which "
                "we should not have received in the first place.\n")
            output.write(
                "    Overall this makes a redundant percentage of "
                f"{percent}\n")
        for data in db.run_query("SELECT * FROM redundancy_summary LIMIT 1"):
            (sum_total, max_total, min_total, avg_total,
                sum_redundant, max_redundant, min_redundant, avg_redundant,
                max_percent, min_percent, avg_percent, global_percent) = cast(
                    Tuple[float, ...], data)
            output.write(
                f"\nThe total packets flown in system was {sum_total}.\n")
            output.write(
                f"    The max, min and average per core was {max_total}, "
                f"{min_total}, {avg_total} packets.\n")
            output.write(
                f"The total redundant packets was {sum_redundant}.\n")
            output.write(
                f"    The max, min and average per core was {max_redundant}, "
                f"{min_redundant}, {avg_redundant} packets.\n")
            output.write(
                "The percentages of redundant packets was "
                f"{global_percent}.\n")
            output.write(
                "    The max and min percentages of redundant packets are"
                f"{max_percent} and {min_percent}.\n")
            output.write(
                "    The average redundant percentages from each core were "
                f"{avg_percent} accordingly.\n")
            break


if __name__ == '__main__':
    print(REDUNDANCY_BY_CORE)
    print(REDUNDANCY_SUMMARY)
