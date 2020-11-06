# Copyright (c) 2017-2019 The University of Manchester
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

from enum import Enum
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary)
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_front_end_common.utilities.utility_objs import ExecutableType

DELAY_EXPANDER_APLX = "delay_expander.aplx"


class DelayExtensionMachineVertex(
        MachineVertex, ProvidesProvenanceDataFromMachineImpl,
        AbstractHasAssociatedBinary):
    __slots__ = [
        "__resources"]

    class _DELAY_EXTENSION_REGIONS(Enum):
        SYSTEM = 0
        DELAY_PARAMS = 1
        PROVENANCE_REGION = 2
        EXPANDER_REGION = 3
        TDMA_REGION = 4

    class EXTRA_PROVENANCE_DATA_ENTRIES(Enum):
        N_PACKETS_RECEIVED = 0
        N_PACKETS_PROCESSED = 1
        N_PACKETS_ADDED = 2
        N_PACKETS_SENT = 3
        N_BUFFER_OVERFLOWS = 4
        N_DELAYS = 5
        N_TIMES_TDMA_FELL_BEHIND = 6

    N_EXTRA_PROVENANCE_DATA_ENTRIES = len(EXTRA_PROVENANCE_DATA_ENTRIES)

    def __init__(self, resources_required, label, constraints=None,
                 app_vertex=None, vertex_slice=None):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
            The resources required by the vertex
        :param str label: The optional name of the vertex
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        """
        super(DelayExtensionMachineVertex, self).__init__(
            label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self.__resources = resources_required

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self._DELAY_EXTENSION_REGIONS.PROVENANCE_REGION.value

    @property
    @overrides(
        ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return self.N_EXTRA_PROVENANCE_DATA_ENTRIES

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               get_provenance_data_from_machine)
    def get_provenance_data_from_machine(self, transceiver, placement):
        # pylint: disable=too-many-locals
        provenance_data = self._read_provenance_data(transceiver, placement)
        provenance_items = self._read_basic_provenance_items(
            provenance_data, placement)
        provenance_data = self._get_remaining_provenance_data_items(
            provenance_data)

        n_packets_received = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_RECEIVED.value]
        n_packets_processed = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_PROCESSED.value]
        n_packets_added = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_ADDED.value]
        n_packets_sent = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_SENT.value]
        n_buffer_overflows = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_BUFFER_OVERFLOWS.value]
        n_delays = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_DELAYS.value]
        n_times_tdma_fell_behind = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_TIMES_TDMA_FELL_BEHIND.value]

        label, x, y, p, names = self._get_placement_details(placement)

        # translate into provenance data items
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_received"),
            n_packets_received))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_processed"),
            n_packets_processed,
            report=n_packets_received != n_packets_processed,
            message=(
                "The delay extension {} on {}, {}, {} only processed {} of {}"
                " received packets.  This could indicate a fault.".format(
                    label, x, y, p, n_packets_processed, n_packets_received))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_added_to_delay_slot"),
            n_packets_added,
            report=n_packets_added != n_packets_processed,
            message=(
                "The delay extension {} on {}, {}, {} only added {} of {}"
                " processed packets.  This could indicate a routing or"
                " filtering fault".format(
                    label, x, y, p, n_packets_added, n_packets_processed))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_sent"),
            n_packets_sent))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Times_the_input_buffer_lost_packets"),
            n_buffer_overflows,
            report=n_buffer_overflows > 0,
            message=(
                "The input buffer for {} on {}, {}, {} lost packets on {} "
                "occasions. This is often a sign that the system is running "
                "too quickly for the number of neurons per core.  Please "
                "increase the timer_tic or time_scale_factor or decrease the "
                "number of neurons per core.".format(
                    label, x, y, p, n_buffer_overflows))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_times_delayed_to_spread_traffic"),
            n_delays))
        provenance_items.append(
            self._app_vertex.get_tdma_provenance_item(
                names, x, y, p, n_times_tdma_fell_behind))

        return provenance_items

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, _partition):
        return self._vertex_slice.n_atoms * self.app_vertex.n_delay_stages

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "delay_extension.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def gen_on_machine(self):
        """ Determine if the given slice needs to be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        if self.app_vertex.delay_generator_data(self.vertex_slice):
            return True
        else:
            return False
