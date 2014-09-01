from data_specification.data_specification_executor import \
    DataSpecificationExecutor
from data_specification.file_data_writer import FileDataWriter
from data_specification.file_data_reader import FileDataReader


from pacman.utilities.progress_bar import ProgressBar


from spinn_machine.sdram import SDRAM
from spinn_machine.virutal_machine import VirtualMachine


from spinnman.messages.scp.scp_signal import SCPSignal
from spinnman.data.file_data_reader import FileDataReader \
    as SpinnmanFileDataReader
from spinnman.model.cpu_state import CPUState
from spinnman import reports as spinnman_reports
from spinnman.transceiver import create_transceiver_from_hostname

from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN import exceptions


import time
import os
import pickle
import ntpath
import logging

logger = logging.getLogger(__name__)


class SpynnakerCommsFunctions(object):

    def __init__(self, reports_states, report_default_directory):
        self._reports_states = reports_states
        self._report_default_directory = report_default_directory
        self._visualiser_creation_utility = None

    def _setup_interfaces(self, hostname, partitionable_graph,
                          visualiser_vertices, machine, partitioned_graph,
                          placements, router_tables, runtime,
                          machine_time_step):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        requires_virtual_board = conf.config.getboolean("Machine",
                                                        "virtual_board")
        requires_visualiser = conf.config.getboolean("Visualiser", "enable")

        if not requires_virtual_board:
            if self._reports_states is None:
                self._txrx = create_transceiver_from_hostname(
                    hostname=hostname, generate_reports=False,
                    discover=False)
            else:
                self._txrx = create_transceiver_from_hostname(
                    hostname=hostname, generate_reports=True,
                    default_report_directory=self._report_default_directory,
                    discover=False)
            #do autoboot if possible
            self._txrx.ensure_board_is_ready(int(conf.config.get("Machine",
                                                                 "version")))
            self._txrx.discover_connections()
            self._machine = self._txrx.get_machine_details()
        else:
            virtual_x_dimension = conf.config.get("Machine",
                                                  "virutal_board_x_dimension")
            virtual_y_dimension = conf.config.get("Machine",
                                                  "virutal_board_y_dimension")
            requires_wrap_around = conf.config.get("Machine",
                                                   "requires_wrap_arounds")
            self._machine = VirtualMachine(
                x_dimension=virtual_x_dimension,
                y_dimension=virtual_y_dimension,
                with_wrap_arounds=requires_wrap_around)

        if requires_visualiser:
            self._visualiser, self._visualiser_vertex_to_page_mapping = \
                self._visualiser_creation_utility.create_visualiser_interface(
                    requires_virtual_board, self._txrx,
                    partitionable_graph, visualiser_vertices, machine,
                    partitioned_graph, placements, router_tables, runtime,
                    machine_time_step)

    def _retieve_provance_data_from_machine(self, executable_targets):
        pass

    def execute_data_specification_execution(self, host_based_execution,
                                             hostname, placements,
                                             graph_mapper):
        if host_based_execution:
            return self.host_based_data_specificiation_execution(
                hostname, placements, graph_mapper)
        else:
            return self._chip_based_data_specificiation_execution(hostname)

    def _chip_based_data_specificiation_execution(self, hostname):
        raise NotImplementedError

    @staticmethod
    def host_based_data_specificiation_execution(hostname, placements,
                                                 graph_mapper):
        space_based_memory_tracker = dict()
        processor_to_app_data_base_address = dict()
         #create a progress bar for end users
        progress_bar = ProgressBar(len(list(placements.placements)),
                                   "on executing data specifications on the "
                                   "host machine")

        for placement in placements.placements:
            associated_vertex = graph_mapper.\
                get_vertex_from_subvertex(placement.subvertex)
            # if the vertex can generate a DSG, call it
            if isinstance(associated_vertex, AbstractDataSpecableVertex):
                data_spec_file_path = \
                    associated_vertex.get_data_spec_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                app_data_file_path = \
                    associated_vertex.get_application_data_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                data_spec_reader = FileDataReader(data_spec_file_path)
                data_writer = FileDataWriter(app_data_file_path)

                #locate current memory requirement
                current_memory_available = SDRAM.DEFAULT_SDRAM_BYTES
                memory_tracker_key = "{}:{}".format(placement.x, placement.y)
                if memory_tracker_key in space_based_memory_tracker.keys():
                    current_memory_available = \
                        space_based_memory_tracker[memory_tracker_key]

                #generate data spec exeuctor
                host_based_data_spec_exeuctor = DataSpecificationExecutor(
                    data_spec_reader, data_writer, current_memory_available)

                #update memory calc and run data spec executor
                bytes_used_by_spec = host_based_data_spec_exeuctor.execute()

                #update base address mapper
                processor_mapping_key = \
                    "{}:{}:{}".format(placement.x, placement.y, placement.p)
                processor_to_app_data_base_address[processor_mapping_key] = \
                    {'start_address':
                        ((SDRAM.DEFAULT_SDRAM_BYTES - current_memory_available)
                         + constants.SDRAM_BASE_ADDR),
                     'memory_used': bytes_used_by_spec}

                space_based_memory_tracker[memory_tracker_key] = \
                    current_memory_available - bytes_used_by_spec

            #update the progress bar
            progress_bar.update()
        #close the progress bar
        progress_bar.end()
        return processor_to_app_data_base_address

    def stop(self, app_id):
        self._txrx.send_signal(app_id, SCPSignal.STOP)
        if conf.config.getboolean("Visualiser", "enable"):
            self._visualiser.stop()

    def _start_execution_on_machine(self, executable_targets, app_id, runtime):
        #deduce how many processors this application uses up
        total_processors = 0
        total_cores = list()
        executable_keys = executable_targets.keys()
        for executable_target in executable_keys:
            core_subsets = executable_targets[executable_target]
            for core_subset in core_subsets:
                total_processors += 1
                total_cores.append(core_subset)

        processor_c_main = self._txrx.get_core_state_count(app_id,
                                                           CPUState.C_MAIN)
        #check that everything has gone though c main to reach sync0 or
        # failing for some unknown reason
        while processor_c_main != 0:
            processor_c_main = self._txrx.get_core_state_count(app_id,
                                                               CPUState.C_MAIN)

        #check that the right number of processors are in sync0
        processors_ready = self._txrx.get_core_state_count(app_id,
                                                           CPUState.SYNC0)


        if processors_ready != total_processors:
            successful_cores, unsucessful_cores = \
                self._break_down_of_failure_to_reach_state(total_cores,
                                                           CPUState.SYNC0)
            #break_down the successful cores and unsuccessful cores into string
            # reps
            break_down = \
                self.turn_break_downs_into_string(
                    total_cores, successful_cores, unsucessful_cores,
                    CPUState.SYNC0)
            raise exceptions.ExecutableFailedToStartException(
                "Only {} processors out of {} have sucessfully reached sync0 "
                "with breakdown of: {}"
                .format(processors_ready, total_processors, break_down))

        # if correct, start applications
        logger.info("Starting application")
        self._txrx.send_signal(app_id, SCPSignal.SYNC0)

        #check all apps have gone into run state
        logger.info("Checking that the application has started")
        processors_running = self._txrx.get_core_state_count(app_id,
                                                             CPUState.RUNNING)
        if processors_running < total_processors:
            sucessful_cores, unsucessful_cores = \
                self._break_down_of_failure_to_reach_state(total_cores,
                                                           CPUState.RUNNING)
            #break_down the successful cores and unsuccessful cores into string
            # reps
            break_down = self.turn_break_downs_into_string(
                total_cores, sucessful_cores, unsucessful_cores,
                CPUState.RUNNING)
            raise exceptions.ExecutableFailedToStartException(
                "Only {} of {} processors started with breakdown {}"
                .format(processors_running, total_processors, break_down))

        #if not running for infinity, check that applications stop correctly
        if runtime is not None:
            logger.info("Application started - waiting for it to stop")
            time.sleep(runtime / 1000.0)
            processors_not_finished = processors_ready
            while processors_not_finished != 0:
                processors_not_finished = \
                    self._txrx.get_core_state_count(app_id,
                                                    CPUState.RUNNING)
                processors_rte = \
                    self._txrx.get_core_state_count(app_id,
                                                    CPUState.RUN_TIME_EXCEPTION)
                if processors_rte > 0:
                    sucessful_cores, unsucessful_cores = \
                        self._break_down_of_failure_to_reach_state(
                            total_cores, CPUState.RUNNING)
                    #break_down the successful cores and unsuccessful cores into
                    #  string reps
                    break_down = self.turn_break_downs_into_string(
                        total_cores, sucessful_cores, unsucessful_cores,
                        CPUState.RUNNING)
                    raise exceptions.ExecutableFailedToStopException(
                        "{} cores have gone into a run time error state with "
                        "breakdown {}.".format(processors_rte, break_down))

            processors_exited =\
                self._txrx.get_core_state_count(app_id, CPUState.FINSHED)

            if processors_exited < total_processors:
                sucessful_cores, unsucessful_cores = \
                        self._break_down_of_failure_to_reach_state(
                            total_cores, CPUState.RUNNING)
                #break_down the successful cores and unsuccessful cores into
                #  string reps
                break_down = self.turn_break_downs_into_string(
                    total_cores, sucessful_cores, unsucessful_cores,
                    CPUState.RUNNING)
                raise exceptions.ExecutableFailedToStopException(
                    "{} of the processors failed to exit successfully with"
                    " breakdown {}.".format(
                        total_processors - processors_exited, break_down))
            logger.info("Application has run to completion")
        else:
            logger.info("Application is set to run forever - PACMAN is exiting")

        if self._reports_states.transciever_report:
            commands = list()
            commands.append("txrx.get_core_state_count({}, CPUState.SYNC0)"
                            .format(app_id))
            commands.append("txrx.send_signal({}, SCPSignal.SYNC0"
                            .format(app_id))
            spinnman_reports.append_to_rerun_script(
                conf.config.get("SpecGeneration", "Binary_folder"),
                commands)

    def _break_down_of_failure_to_reach_state(self, total_cores, state):
        sucessful_cores = list()
        unsucessful_cores = dict()
        core_infos = self._txrx.get_cpu_information(total_cores)
        for core_info in core_infos:
            if core_info.state == state:
                sucessful_cores.append((core_info.x, core_info.y, core_info.p))
            else:
                unsucessful_cores[(core_info.x, core_info.y,core_info.p)] = \
                    core_info.state
        return sucessful_cores, unsucessful_cores

    @staticmethod
    def turn_break_downs_into_string(total_cores, successful_cores,
                                     unsuccessful_cores, state):
        break_down = os.linesep
        for core_info in total_cores:
            for processor_id in core_info.processor_ids:
                core_coord = (core_info.x, core_info.y, processor_id)
                if core_coord in successful_cores:
                    break_down += "{}:{}:{} sucessfully in state {}{}"\
                        .format(core_info.x, core_info.y, processor_id, state,
                                os.linesep)
                else:
                    real_state = \
                        unsuccessful_cores[(core_info.x, core_info.y,
                                           processor_id)]
                    break_down += \
                        "{}:{}:{} failed to be in state {} and was in " \
                        "state {} instead{}"\
                        .format(core_info.x, core_info.y, processor_id,
                                state, real_state, os.linesep)
        return break_down

    def _load_application_data(self, placements, vertex_to_subvertex_mapper,
                               processor_to_app_data_base_address, hostname):

        #if doing reload, start script
        if self._reports_states.transciever_report:
            spinnman_reports.start_transceiver_rerun_script(
                conf.config.get("SpecGeneration", "Binary_folder"), hostname)

        #go through the placements and see if theres any application data to
        # load
        for placement in placements.placements:
            associated_vertex = \
                vertex_to_subvertex_mapper.get_vertex_from_subvertex(
                    placement.subvertex)

            if isinstance(associated_vertex, AbstractDataSpecableVertex):
                key = "{}:{}:{}".format(placement.x, placement.y, placement.p)
                start_address = \
                    processor_to_app_data_base_address[key]['start_address']
                memory_used = \
                    processor_to_app_data_base_address[key]['memory_used']
                file_path_for_application_data = \
                    associated_vertex.get_application_data_file_name(
                        placement.x, placement.y, placement.p, hostname)
                application_data_file_reader = \
                    SpinnmanFileDataReader(file_path_for_application_data)
                self._txrx.write_memory(placement.x, placement.y, start_address,
                                        application_data_file_reader,
                                        memory_used)
                #update user 0 so that it points to the start of the \
                # applications data region on sdram

                user_o_register_address = \
                    self._txrx.get_user_0_register_address_from_core(
                        placement.x, placement.y, placement.p)
                self._txrx.write_memory(placement.x, placement.y,
                                        user_o_register_address, start_address)

                #add lines to rerun_script if requested
                if self._reports_states.transciever_report:
                    lines = list()
                    lines.append("application_data_file_reader = "
                                 "SpinnmanFileDataReader(\"{}\")"
                                 .format(ntpath.basename(
                                 file_path_for_application_data)))

                    lines.append("txrx.write_memory({}, {}, {}, "
                                 "application_data_file_reader, {})"
                                 .format(
                                 placement.x, placement.y, start_address,
                                 memory_used))
                    spinnman_reports.append_to_rerun_script(
                        conf.config.get("SpecGeneration", "Binary_folder"),
                        lines)

    def _load_executable_images(self, executable_targets, app_id):
        """
        go through the exeuctable targets and load each binary to everywhere and
        then set each given core to sync0 that require it
        """
        if self._reports_states.transciever_report:
            pickled_point = os.path.join(conf.config.get("SpecGeneration",
                                                         "Binary_folder"),
                                         "picked_executables_mappings")
            pickle.dump(executable_targets, open(pickled_point, 'wb'))
            lines = list()
            lines.append("executable_targets = pickle.load(open(\"{}\", "
                         "\"rb\"))".format(ntpath.basename(pickled_point)))
            spinnman_reports.append_to_rerun_script(conf.config.get(
                "SpecGeneration", "Binary_folder"), lines)

        for exectuable_target_key in executable_targets.keys():
            file_reader = SpinnmanFileDataReader(exectuable_target_key)
            core_subset = executable_targets[exectuable_target_key]

            # for some reason, we have to hand the size of a binary. The only
            #logical way to do this is to read the exe and determine the length
            #. TODO this needs to change so that the trasnciever figures this out
            #itself

            # TODO FIX THIS CHUNK
            statinfo = os.stat(exectuable_target_key)
            file_to_read_in = open(exectuable_target_key, 'rb')
            buf = file_to_read_in.read(statinfo.st_size)
            size = (len(buf))

            self._txrx.execute_flood(core_subset, file_reader, app_id,
                                     size)

            if self._reports_states.transciever_report:
                lines = list()
                lines.append("core_subset = executable_targets[\"{}\"]"
                             .format(exectuable_target_key))
                lines.append("file_reader = SpinnmanFileDataReader(\"{}\")"
                             .format(exectuable_target_key))
                lines.append("txrx.execute_flood(core_subset, file_reader"
                             ", {}, {})".format(app_id, size))
                spinnman_reports.append_to_rerun_script(conf.config.get(
                    "SpecGeneration", "Binary_folder"), lines)