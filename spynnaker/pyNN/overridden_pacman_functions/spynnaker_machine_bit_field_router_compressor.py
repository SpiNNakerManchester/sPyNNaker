import logging

from spinn_front_end_common.abstract_models.\
    abstract_supports_bit_field_generation import \
    AbstractSupportsBitFieldGeneration
from spinn_front_end_common.interface.interface_functions import \
    ChipIOBufExtractor
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import \
    MachineBitFieldRouterCompressor
from spinn_front_end_common.utilities import system_control_logic
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.utility_models.synapse_expander. \
    synapse_expander import SYNAPSE_EXPANDER

logger = logging.getLogger(__name__)


class SpynnakerMachineBitFieldRouterCompressor(object):

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph, graph_mapper,
            placements, executable_finder, read_algorithm_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            machine_time_step, time_scale_factor,
            no_sync_changes, threshold_percentage,
            executable_targets, compress_only_when_needed=True,
            compress_as_much_as_possible=False,  provenance_data_objects=None):
        """ entrance for routing table compression with bit field

        :param routing_tables: routing tables
        :param transceiver: spinnman instance
        :param machine: spinnMachine instance
        :param app_id: app id of the application
        :param provenance_file_path: file path for prov data
        :param machine_graph: machine graph
        :param graph_mapper: mapping between graphs
        :param placements: placements on machine
        :param threshold_percentage: the percentage of bitfields to do on chip\
         before its considered a success
        :param executable_finder: where are binaries are located
        :param read_algorithm_iobuf: bool flag saying if read iobuf
        :param compress_only_when_needed: bool flag asking if compress only \
        when needed
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :rtype: None
        """

        # build machine compressor
        machine_bit_field_router_compressor = MachineBitFieldRouterCompressor()
        (compressor_executable_targets, prov_items) = \
            machine_bit_field_router_compressor(
                routing_tables=routing_tables, transceiver=transceiver,
                machine=machine, app_id=app_id,
                provenance_file_path=provenance_file_path,
                machine_graph=machine_graph, graph_mapper=graph_mapper,
                placements=placements, executable_finder=executable_finder,
                read_algorithm_iobuf=read_algorithm_iobuf,
                produce_report=produce_report,
                default_report_folder=default_report_folder,
                target_length=target_length, routing_infos=routing_infos,
                time_to_try_for_each_iteration=time_to_try_for_each_iteration,
                use_timer_cut_off=use_timer_cut_off,
                machine_time_step=machine_time_step,
                time_scale_factor=time_scale_factor,
                no_sync_changes=no_sync_changes,
                threshold_percentage=threshold_percentage,
                compress_only_when_needed=compress_only_when_needed,
                compress_as_much_as_possible=compress_as_much_as_possible,
                executable_targets=executable_targets)

        # adjust cores to exclude the ones which did not give sdram.
        expander_chip_cores = self._locate_synaptic_expander_cores(
            compressor_executable_targets, executable_finder,
            placements, graph_mapper, machine)

        # just rerun the synaptic expander for safety purposes
        self._rerun_synaptic_cores(
            expander_chip_cores, transceiver, provenance_file_path,
            executable_finder, True, no_sync_changes)

        return prov_items

    @staticmethod
    def _locate_synaptic_expander_cores(
            cores, executable_finder, placements, graph_mapper, machine):
        """ removes host based cores for synaptic matrix regeneration

        :param cores: the cores for everything
        :param executable_finder: way to get binary path
        :param graph_mapper: mapping between graphs
        :param machine: spiNNMachine instance.
        :return: new targets for synaptic expander
        """
        new_cores = ExecutableTargets()

        # locate expander executable path
        expander_executable_path = executable_finder.get_executable_path(
            SYNAPSE_EXPANDER)

        # if any ones are going to be ran on host, ignore them from the new
        # core setup
        for core_subset in cores.all_core_subsets:
            chip = machine.get_chip_at(core_subset.x, core_subset.y)
            for processor_id in range(0, chip.n_processors):
                if placements.is_processor_occupied(
                        core_subset.x, core_subset.y, processor_id):
                    vertex = placements.get_vertex_on_processor(
                        core_subset.x, core_subset.y, processor_id)
                    app_vertex = graph_mapper.get_application_vertex(vertex)
                    if isinstance(
                            app_vertex, AbstractSupportsBitFieldGeneration):
                        if app_vertex.gen_on_machine(
                                graph_mapper.get_slice(vertex)):
                            new_cores.add_processor(
                                expander_executable_path, core_subset.x,
                                core_subset.y, processor_id)
        return new_cores

    def _rerun_synaptic_cores(
            self, synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder, needs_sync_barrier,
            no_sync_changes):
        """ reruns the synaptic expander

        :param synaptic_expander_rerun_cores: the cores to rerun the synaptic /
        matrix generator for
        :param transceiver: spinnman instance
        :param provenance_file_path: prov file path
        :param executable_finder: finder of binary file paths
        :rtype: None
        """
        if synaptic_expander_rerun_cores.total_processors != 0:
            logger.info("rerunning synaptic expander")
            expander_app_id = transceiver.app_id_tracker.get_new_id()
            system_control_logic.run_system_application(
                synaptic_expander_rerun_cores, expander_app_id, transceiver,
                provenance_file_path, executable_finder, True, None,
                self._handle_failure_for_synaptic_expander_rerun,
                [CPUState.FINISHED], needs_sync_barrier, no_sync_changes)

    def _handle_failure_for_synaptic_expander_rerun(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the state where some cores have failed.

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
        logger.info("rerunning of the synaptic expander has failed")
        self._call_iobuf_and_clean_up(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder)

    @staticmethod
    def _call_iobuf_and_clean_up(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the reading of iobuf and cleaning the cores off the machine

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
        iobuf_extractor = ChipIOBufExtractor()
        io_errors, io_warnings = iobuf_extractor(
            transceiver, executable_targets, executable_finder,
            provenance_file_path)
        for warning in io_warnings:
            logger.warning(warning)
        for error in io_errors:
            logger.error(error)
        transceiver.stop_application(compressor_app_id)
        transceiver.app_id_tracker.free_id(compressor_app_id)
