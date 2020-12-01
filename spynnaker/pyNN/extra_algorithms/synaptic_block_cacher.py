# Copyright (c) 2020-2021 The University of Manchester
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
import struct

from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState


class SynapticBlockCacher(object):

    __slots__ = ("__aplx", "__placements", "__txrx")

    # bit field report file names
    _SYNAPTIC_CACHER_REPORT_FILENAME = "cached_synaptic_blocks.rpt"

    # binary name
    _SYNAPTIC_CACHER_APLX = "synaptic_block_cacher.aplx"

    # progress bar name
    _PROGRESS_BAR_NAME = (
        "Running search for synaptic blocks worth caching in DTCM.")

    _REPORT_PROGRESS_BAR_NAME = (
        "Generating synaptic block cacher report.")

    # struct holder
    _ONE_WORD = struct.Struct("<I")

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

    def __call__(
            self, placements, executable_finder, provenance_file_path,
            transceiver, write_synaptic_block_cacher_iobuf,
            default_report_folder, machine_graph,
            write_synaptic_block_cacher_report):
        """ Loads and runs the bit field generator on chip.

        :param ~.Placements placements: placements
        :param ~.ExecutableFinder executable_finder: the executable finder
        :param str provenance_file_path:
            the path to where provenance data items is written
        :param ~.Transceiver transceiver: the SpiNNMan instance
        :param str default_report_folder: the file path for reports
        :param ~.MachineGraph machine_graph: the machine graph
        :param bool write_synaptic_block_cacher_iobuf: flag for reading iobuf.
        :param bool write_synaptic_block_cacher_report:
            flag for generating report
        """

        self.__txrx = transceiver
        self.__placements = placements
        self.__aplx = executable_finder.get_executable_path(
            self._SYNAPTIC_CACHER_APLX)

        # progress bar
        progress = ProgressBar(
            (machine_graph.n_vertices * 2) + 1, self._PROGRESS_BAR_NAME)

        cores_to_target = self._calculate_core_data(machine_graph, progress)

        # load data
        synaptic_block_cacher_app_id = transceiver.app_id_tracker.get_new_id()
        progress.update(1)

        # run app
        system_control_logic.run_system_application(
            cores_to_target, synaptic_block_cacher_app_id, transceiver,
            provenance_file_path, executable_finder,
            write_synaptic_block_cacher_iobuf, self.__check_for_success,
            [CPUState.FINISHED], False,
            "bit_field_expander_on_{}_{}_{}.txt", progress_bar=progress)
        # update progress bar
        progress.end()

        # write report if needed
        if write_synaptic_block_cacher_report:
            progress = ProgressBar(
                machine_graph.n_vertices, self._REPORT_PROGRESS_BAR_NAME)
            file_path = os.path.join(
                default_report_folder,
                self._SYNAPTIC_CACHER_REPORT_FILENAME)
            with open(file_path, "w") as output:
                for vertex in progress.over(machine_graph.vertices):
                    if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                        self._report_vertex(vertex, output)

    def _report_vertex(self, machine_vertex, output):
        """ reads master pop table in sdram and checks how many synaptic\
         blocks have been decided to be cached vs not cached.

        :param ~MachineVertex machine_vertex: the machine vertex to read
        :param Stream output: the file to write to
        :rtype: None
        """
        pass

    def _calculate_core_data(self, machine_graph, progress):
        """ gets the data needed for the bit field expander for the machine

        :param ~.MachineGraph machine_graph: machine graph
        :param ~.ProgressBar progress: progress bar
        :return: data and expander cores
        :rtype: ~.ExecutableTargets
        """
        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # bit field expander executable file path
        # locate vertices which can have a synaptic matrix to begin with
        for vertex in progress.over(machine_graph.vertices, False):
            if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                placement = self.__placements.get_placement_of_vertex(vertex)
                self.__write_single_core_data(placement, expander_cores)

    def __write_single_core_data(self, placement, expander_cores):
        """
        :param ~.Placement placement:
        :param ~.ExecutableTargets expander_cores:
        """
        # check if the chip being considered already.
        expander_cores.add_processor(
            self.__aplx, placement.x, placement.y, placement.p,
            executable_type=ExecutableType.SYSTEM)

        bit_field_builder_region = placement.vertex.bit_field_builder_region(
            self.__txrx, placement)
        # update user 1 with location
        user_1_base_address = (
            self.__txrx.get_user_1_register_address_from_core(placement.p))
        self.__txrx.write_memory(
            placement.x, placement.y, user_1_base_address,
            self._ONE_WORD.pack(bit_field_builder_region), self._ONE_WORD.size)

    def __check_for_success(self, executable_targets, transceiver):
        """ Goes through the cores checking for cores that have failed to\
            expand the bitfield to the core

        :param ~.ExecutableTargets executable_targets:
            cores to load bitfield on
        :param ~.Transceiver transceiver: SpiNNMan instance
        :rtype: bool
        """
        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:
                # Read the result from USER0 register
                user_2_base_address = \
                    transceiver.get_user_2_register_address_from_core(p)
                result, = self._ONE_WORD.unpack(transceiver.read_memory(
                    x, y, user_2_base_address, self._ONE_WORD.size))

                # The result is 0 if success, otherwise failure
                if result != self._SUCCESS:
                    return False
        return True
