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

import logging
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.overrides import overrides
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import (
        MachineBitFieldPairRouterCompressor,
        MachineBitFieldUnorderedRouterCompressor)
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from .synapse_expander import SYNAPSE_EXPANDER

logger = logging.getLogger(__name__)


@add_metaclass(AbstractBase)
class SpynnakerMachineBitFieldRouterCompressor(object):
    """ Bitfield-aware on-machine routing table compression algorithm.

    :param ~pacman.model.routing_tables.MulticastRoutingTables routing_tables:
        routing tables
    :param ~spinnman.transceiver.Transceiver transceiver: spinnman instance
    :param ~spinn_machine.Machine machine: spinnMachine instance
    :param int app_id: app id of the application
    :param str provenance_file_path: file path for prov data
    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        machine graph
    :param ~pacman.model.placements.Placements placements:
        placements on machine
    :param int threshold_percentage:
        the percentage of bitfields to do on chip before its considered a
        success
    :param executable_finder: where are binaries are located
    :type executable_finder:
        ~spinn_front_end_common.utilities.utility_objs.ExecutableFinder
    :param bool read_algorithm_iobuf: flag saying if read iobuf
    :param bool compress_as_much_as_possible:
        flag asking if should compress as much as possible
    :param bool read_expander_iobuf: reads the synaptic expander iobuf.
    """

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph,
            placements, executable_finder, read_algorithm_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            machine_time_step, time_scale_factor, threshold_percentage,
            executable_targets, read_expander_iobuf,
            compress_as_much_as_possible=False, provenance_data_objects=None):
        """ entrance for routing table compression with bit field

        :param ~.MulticastRoutingTables routing_tables:
        :param ~.Transceiver transceiver:
        :param ~.Machine machine:
        :param int app_id:
        :param str provenance_file_path:
        :param ~.MachineGraph machine_graph:
        :param ~.Placements placements:
        :param int threshold_percentage:
        :param ~.ExecutableFinder executable_finder:
        :param bool read_algorithm_iobuf:
        :param bool compress_as_much_as_possible:
        :param bool read_expander_iobuf:
        """
        # build machine compressor
        machine_bit_field_router_compressor = self.compressor_factory()
        (compressor_executable_targets, prov_items) = \
            machine_bit_field_router_compressor(
                routing_tables=routing_tables, transceiver=transceiver,
                machine=machine, app_id=app_id,
                provenance_file_path=provenance_file_path,
                machine_graph=machine_graph,
                placements=placements, executable_finder=executable_finder,
                read_algorithm_iobuf=read_algorithm_iobuf,
                produce_report=produce_report,
                default_report_folder=default_report_folder,
                target_length=target_length, routing_infos=routing_infos,
                time_to_try_for_each_iteration=time_to_try_for_each_iteration,
                use_timer_cut_off=use_timer_cut_off,
                machine_time_step=machine_time_step,
                time_scale_factor=time_scale_factor,
                threshold_percentage=threshold_percentage,
                compress_as_much_as_possible=compress_as_much_as_possible,
                executable_targets=executable_targets)

        # adjust cores to exclude the ones which did not give sdram.
        expander_chip_cores = self._locate_synaptic_expander_cores(
            compressor_executable_targets, executable_finder,
            placements, machine)

        # just rerun the synaptic expander for safety purposes
        self._rerun_synaptic_cores(
            expander_chip_cores, transceiver, provenance_file_path,
            executable_finder, True, read_expander_iobuf)

        return prov_items

    @abstractmethod
    def compressor_factory(self):
        """ Creates the specific compressor to use.

        :rtype: MachineBitFieldRouterCompressor
        """

    def _locate_synaptic_expander_cores(
            self, cores, executable_finder, placements, machine):
        """ removes host based cores for synaptic matrix regeneration

        :param ~.ExecutableTargets cores: the cores for everything
        :param ~.ExecutableFinder executable_finder: way to get binary path
        :param ~.Machine machine: spiNNMachine instance.
        :return: new targets for synaptic expander
        :rtype: ~.ExecutableTargets
        """
        new_cores = ExecutableTargets()

        # locate expander executable path
        expander_executable_path = executable_finder.get_executable_path(
            SYNAPSE_EXPANDER)

        # if any ones are going to be ran on host, ignore them from the new
        # core setup
        for core_subset in cores.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in range(machine.get_chip_at(x, y).n_processors):
                if self._gen_bitfield_on_machine(placements, x, y, p):
                    new_cores.add_processor(
                        expander_executable_path, x, y, p,
                        executable_type=ExecutableType.SYSTEM)
        return new_cores

    @staticmethod
    def _gen_bitfield_on_machine(placements, x, y, p):
        """ Check if the given core's vertex has bitfields generated on\
            machine.

        :param ~.Placements placements:
        :param int x:
        :param int y:
        :param int p:
        :rtype: bool
        """
        if placements.is_processor_occupied(x, y, p):
            vertex = placements.get_vertex_on_processor(x, y, p)
            if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                if vertex.app_vertex.gen_on_machine(vertex.vertex_slice):
                    return True
        return False

    @staticmethod
    def _rerun_synaptic_cores(
            synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder, needs_sync_barrier,
            read_expander_iobuf):
        """ reruns the synaptic expander

        :param ~.ExecutableTargets synaptic_expander_rerun_cores:
            the cores to rerun the synaptic matrix generator for
        :param ~.Transceiver transceiver: spinnman instance
        :param str provenance_file_path: prov file path
        :param ~.ExecutableFinder executable_finder:
            finder of binary file paths
        :param bool read_expander_iobuf: read off iobuf if needed
        """
        if synaptic_expander_rerun_cores.total_processors != 0:
            logger.info("rerunning synaptic expander")
            expander_app_id = transceiver.app_id_tracker.get_new_id()
            system_control_logic.run_system_application(
                synaptic_expander_rerun_cores, expander_app_id, transceiver,
                provenance_file_path, executable_finder, read_expander_iobuf,
                None, [CPUState.FINISHED], needs_sync_barrier,
                "rerun_of_synaptic_expander_on_{}_{}_{}.txt")


class SpynnakerMachineBitFieldUnorderedRouterCompressor(
        SpynnakerMachineBitFieldRouterCompressor):

    @overrides(SpynnakerMachineBitFieldRouterCompressor.compressor_factory)
    def compressor_factory(self):
        return MachineBitFieldUnorderedRouterCompressor()


class SpynnakerMachineBitFieldPairRouterCompressor(
        SpynnakerMachineBitFieldRouterCompressor):

    @overrides(SpynnakerMachineBitFieldRouterCompressor.compressor_factory)
    def compressor_factory(self):
        return MachineBitFieldPairRouterCompressor()
