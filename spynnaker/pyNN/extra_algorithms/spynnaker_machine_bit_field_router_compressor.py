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
from spinn_front_end_common.abstract_models.\
    abstract_supports_bit_field_generation import \
    AbstractSupportsBitFieldGeneration
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import (
        MachineBitFieldPairRouterCompressor,
        MachineBitFieldUnorderedRouterCompressor)
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)

logger = logging.getLogger(__name__)


@add_metaclass(AbstractBase)
class SpynnakerMachineBitFieldRouterCompressor(object):

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph,
            placements, executable_finder, write_compressor_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            machine_time_step, time_scale_factor, threshold_percentage,
            executable_targets, read_expander_iobuf,
            compress_as_much_as_possible=False, provenance_data_objects=None):
        """ entrance for routing table compression with bit field

        :param routing_tables: routing tables
        :param transceiver: spinnman instance
        :param machine: spinnMachine instance
        :param app_id: app id of the application
        :param provenance_file_path: file path for prov data
        :param machine_graph: machine graph
        :param placements: placements on machine
        :param threshold_percentage: the percentage of bitfields to do on chip\
         before its considered a success
        :param executable_finder: where are binaries are located
        :param read_algorithm_iobuf: bool flag saying if read iobuf
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :param read_expander_iobuf: reads the synaptic expander iobuf.
        :rtype: None
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
                write_compressor_iobuf=write_compressor_iobuf,
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
        "Method to call the specific compressor to use"

    @staticmethod
    def _locate_synaptic_expander_cores(
            cores, executable_finder, placements, machine):
        """ removes host based cores for synaptic matrix regeneration

        :param cores: the cores for everything
        :param executable_finder: way to get binary path
        :param machine: spiNNMachine instance.
        :return: new targets for synaptic expander
        """
        new_cores = ExecutableTargets()

        # locate expander executable path
        expander_executable_path = executable_finder.get_executable_path(
            SYNAPSE_EXPANDER_APLX)

        # if any ones are going to be ran on host, ignore them from the new
        # core setup
        for core_subset in cores.all_core_subsets:
            chip = machine.get_chip_at(core_subset.x, core_subset.y)
            for processor_id in range(0, chip.n_processors):
                if placements.is_processor_occupied(
                        core_subset.x, core_subset.y, processor_id):
                    vertex = placements.get_vertex_on_processor(
                        core_subset.x, core_subset.y, processor_id)
                    if (isinstance(vertex, AbstractSupportsBitFieldGeneration)
                            and isinstance(vertex, AbstractSynapseExpandable)
                            and vertex.gen_on_machine()):
                        new_cores.add_processor(
                            expander_executable_path,
                            core_subset.x, core_subset.y, processor_id,
                            executable_type=ExecutableType.SYSTEM)
        return new_cores

    @staticmethod
    def _rerun_synaptic_cores(
            synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder, needs_sync_barrier,
            read_expander_iobuf):
        """ reruns the synaptic expander

        :param synaptic_expander_rerun_cores: the cores to rerun the synaptic /
        matrix generator for
        :param transceiver: spinnman instance
        :param provenance_file_path: prov file path
        :param executable_finder: finder of binary file paths
        :param read_expander_iobuf: bool for reading off iobuf if needed
        :rtype: None
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
