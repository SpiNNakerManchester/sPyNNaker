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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import (
        MachineBitFieldPairRouterCompressor,
        MachineBitFieldOrderedCoveringCompressor)
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractMachineBitFieldRouterCompressor(object, metaclass=AbstractBase):
    """ Algorithm that adds in regeneration of synaptic matrices to bitfield\
    compression to\
    :py:class:`spinn_front_end_common.interface.interface_functions.\
    MachineBitFieldRouterCompressor`
    """

    _RERUN_IOBUF_NAME_PATTERN = "rerun_of_synaptic_expander_on_{}_{}_{}.txt"

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph,
            placements, executable_finder, write_compressor_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            machine_time_step, time_scale_factor, threshold_percentage,
            retry_count, executable_targets, read_expander_iobuf,
            compress_as_much_as_possible=False, provenance_data_objects=None):
        """ entrance for routing table compression with bit field

        :param routing_tables: routing tables
        :type routing_tables:
            ~pacman.model.routing_tables.MulticastRoutingTables
        :param ~spinnman.transceiver.Transceiver transceiver: spinnman instance
        :param ~spinn_machine.Machine machine: spinnMachine instance
        :param int app_id: app id of the application
        :param str provenance_file_path: file path for prov data
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            machine graph
        :param ~pacman.model.placements.Placements placements:
            placements on machine
        :param executable_finder: where are binaries are located
        :type executable_finder:
            ~spinn_front_end_common.utilities.utility_objs.ExecutableFinder
        :param bool write_compressor_iobuf: flag saying if read iobuf
        :param bool produce_report:
        :param str default_report_folder:
        :param int target_length:
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        :param int threshold_percentage:
            the percentage of bitfields to do on chip before its considered
            a success
        :param retry_count:
            Number of times that the sorters should set of the compressions
            again. None for as much as needed
        :type retry_count: int or None
        :param bool read_algorithm_iobuf: flag saying if read iobuf
        :param bool compress_as_much_as_possible:
            flag asking if should compress as much as possible
        :param bool read_expander_iobuf: reads the synaptic expander iobuf.
        :rtype:
            list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """

        # build machine compressor
        machine_bit_field_router_compressor = self._compressor_factory()
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
                retry_count=retry_count,
                compress_as_much_as_possible=compress_as_much_as_possible,
                executable_targets=executable_targets,
                provenance_data_objects=provenance_data_objects)

        # adjust cores to exclude the ones which did not give sdram.
        expander_chip_cores = self._locate_expander_rerun_targets(
            compressor_executable_targets, executable_finder, placements,
            transceiver)

        # just rerun the synaptic expander for safety purposes
        self._rerun_synaptic_cores(
            expander_chip_cores, transceiver, provenance_file_path,
            executable_finder, True, read_expander_iobuf)

        return prov_items

    @abstractmethod
    def _compressor_factory(self):
        "Method to call the specific compressor to use"

    def _locate_expander_rerun_targets(
            self, bitfield_targets, executable_finder, placements,
            transceiver):
        """ removes host based cores for synaptic matrix regeneration

        :param ~.ExecutableTargets bitfield_targets: the cores that were used
        :param ~.ExecutableFinder executable_finder: way to get binary path
        :param ~.Placements placements: placements on machine
        :param ~.Transceiver transceiver: spinnman instance
        :return: new targets for synaptic expander
        :rtype: ~.ExecutableTargets
        """

        # locate expander executable path
        expander_executable_path = executable_finder.get_executable_path(
            SYNAPSE_EXPANDER_APLX)

        # if any ones are going to be ran on host, ignore them from the new
        # core setup
        new_cores = ExecutableTargets()
        for placement in self.__machine_expandables(
                bitfield_targets.all_core_subsets, placements):
            new_cores.add_processor(
                expander_executable_path,
                placement.x, placement.y, placement.p,
                executable_type=ExecutableType.SYSTEM)
            # Write the region to USER1, as that is the best we can do
            write_address_to_user1(
                transceiver, placement.x, placement.y, placement.p,
                placement.vertex.connection_generator_region)
        return new_cores

    @staticmethod
    def __machine_expandables(cores, placements):
        """
        :param ~.CoreSubsets cores:
        :param ~.Placements placements:
        :rtype: iterable(~.Placement)
        """
        for place in placements.placements:
            vertex = place.vertex
            if (cores.is_core(place.x, place.y, place.p)
                    # Have we overwritten it?
                    and isinstance(vertex, AbstractSupportsBitFieldGeneration)
                    # Can we fix it by rerunning?
                    and isinstance(vertex, AbstractSynapseExpandable)
                    and vertex.gen_on_machine()):
                yield place

    @classmethod
    def _rerun_synaptic_cores(
            cls, synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder, needs_sync_barrier,
            read_expander_iobuf):
        """ reruns the synaptic expander

        :param ~.ExecutableTargets synaptic_expander_rerun_cores:
            the cores to rerun the synaptic matrix generator for
        :param ~.Transceiver transceiver: spinnman instance
        :param str provenance_file_path: prov file path
        :param ~.ExecutableFinder executable_finder:
            finder of binary file paths
        :param bool needs_sync_barrier:
        :param bool read_expander_iobuf: whether to read off iobuf if needed
        """
        if synaptic_expander_rerun_cores.total_processors:
            logger.info("rerunning synaptic expander")
            expander_app_id = transceiver.app_id_tracker.get_new_id()
            run_system_application(
                synaptic_expander_rerun_cores, expander_app_id, transceiver,
                provenance_file_path, executable_finder, read_expander_iobuf,
                None, [CPUState.FINISHED], needs_sync_barrier,
                cls._RERUN_IOBUF_NAME_PATTERN)


class SpynnakerMachineBitFieldOrderedCoveringCompressor(
        AbstractMachineBitFieldRouterCompressor):
    @overrides(AbstractMachineBitFieldRouterCompressor._compressor_factory)
    def _compressor_factory(self):
        return MachineBitFieldOrderedCoveringCompressor()


class SpynnakerMachineBitFieldUnorderedRouterCompressor(
        SpynnakerMachineBitFieldOrderedCoveringCompressor):
    """ DEPRACATED use SpynnakerMachineBitFieldOrderedCoveringCompressor """

    def __new__(cls, *args, **kwargs):
        logger.warning(
            "SpynnakerMachineBitFieldUnorderedRouterCompressor "
            "algorithm name is deprecated. "
            "Please use SpynnakerMachineBitFieldOrderedCoveringCompressor "
            "instead. "
            "Remove algorithms from your cfg to use defaults")
        return super().__new__(cls, *args, **kwargs)

    @overrides(AbstractMachineBitFieldRouterCompressor._compressor_factory)
    def _compressor_factory(self):
        return MachineBitFieldOrderedCoveringCompressor()


class SpynnakerMachineBitFieldPairRouterCompressor(
        AbstractMachineBitFieldRouterCompressor):
    @overrides(AbstractMachineBitFieldRouterCompressor._compressor_factory)
    def _compressor_factory(self):
        return MachineBitFieldPairRouterCompressor()
