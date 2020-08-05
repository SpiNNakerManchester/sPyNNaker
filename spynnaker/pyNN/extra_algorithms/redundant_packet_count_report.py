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
    """ Reports how many packets were filtered by the packet filtering.

    :param provenance_items:
        the collected provenance
    :type provenance_items:
        list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
    :param str report_default_directory: where to write reports
    """

    # The name of the report we create
    _FILE_NAME = "redundant_packet_count.rpt"

    # The provenance items we care about for a vertex
    _RELEVANT = frozenset([
        PopulationMachineVertex.GHOST_SEARCHES,
        PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS,
        PopulationMachineVertex.INVALID_MASTER_POP_HITS,
        PopulationMachineVertex.SPIKES_PROCESSED])

    def __call__(self, provenance_items, report_default_directory):
        """
        :param list(~.ProvenanceDataItem) provenance_items:
        :param str report_default_directory:
        """
        file_name = os.path.join(report_default_directory, self._FILE_NAME)

        try:
            with open(file_name, "w") as f:
                self._write_report(f, provenance_items)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Generate_placement_reports: Can't open file"
                             " {} for writing.", self._FILE_NAME)

    def _write_report(self, output, provenance_items):
        data = defaultdict(dict)
        for provenance_item in provenance_items:
            last_name = provenance_item.names[-1]
            key = provenance_item.names[0]
            if last_name in self._RELEVANT:
                # add to store
                data[key][last_name] = provenance_item.value
                # accum enough data on a core to do summary
                if len(data[key]) == len(self._RELEVANT):
                    self.__write_core_summary(key, data[key], output)

    @staticmethod
    def __write_core_summary(key, items, output):
        """
        :param str key: The name of the core
        :param dict items: The relevant items for a core
        :param ~io.TextIOBase output:
        """
        # Extract
        ghosts = items[PopulationMachineVertex.GHOST_SEARCHES]
        filtered = items[PopulationMachineVertex.BIT_FIELD_FILTERED_PACKETS]
        invalid = items[PopulationMachineVertex.INVALID_MASTER_POP_HITS]
        spikes = items[PopulationMachineVertex.SPIKES_PROCESSED]

        # total packets received
        total = ghosts + filtered + invalid + spikes

        # total redundant packets
        redundant = ghosts + filtered + invalid

        percentage = 0
        if total != 0:
            percentage = (100.0 / total) * redundant

        output.write(
            "core {}\n\n"
            "    {} packets received.\n"
            "    {} were detected as redundant packets by the bitfield "
            "filter.\n"
            "    {} were detected as having no targets after the DMA stage.\n"
            "    {} were detected as packets which we should not have "
            "received in the first place.\n"
            "    Overall this makes a redundant percentage of {}\n".format(
                key, total, filtered, ghosts, invalid, percentage))
