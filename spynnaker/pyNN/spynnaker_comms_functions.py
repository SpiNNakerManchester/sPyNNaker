from data_specification.data_specification_executor import \
    DataSpecificationExecutor
from data_specification.file_data_writer import FileDataWriter
from data_specification.file_data_reader import FileDataReader


from pacman.utilities.progress_bar import ProgressBar
from spinn_machine.diagnostic_filter import DiagnosticFilter

from spinn_machine.sdram import SDRAM
from spinn_machine.virutal_machine import VirtualMachine


from spinnman.messages.scp.scp_signal import SCPSignal
from spinnman.model.cpu_state import CPUState
from spinnman.transceiver import create_transceiver_from_hostname
from spinnman.data.file_data_reader import FileDataReader \
    as SpinnmanFileDataReader
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import reports


import time
import os
import logging

logger = logging.getLogger(__name__)


class SpynnakerCommsFunctions(object):

    def __init__(self, reports_states, report_default_directory):
        self._reports_states = reports_states
        self._report_default_directory = report_default_directory
        self._iptags = list()
        self._reverse_iptags = list()
        self._machine = None

    def _setup_interfaces(self, hostname):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        requires_virtual_board = conf.config.getboolean("Machine",
                                                        "virtual_board")

        if not requires_virtual_board:
            ignored_chips = None
            ignored_cores = None
            downed_chips = str(conf.config.get("Machine", "down_chips"))
            if downed_chips is not None and downed_chips != "None":
                ignored_chips = CoreSubsets()
                for downed_chip in downed_chips.split(":"):
                    x, y = downed_chip.split(",")
                    ignored_chips.add_core_subset(CoreSubset(int(x), int(y),
                                                             []))
            downed_cores = str(conf.config.get("Machine", "down_cores"))
            if downed_cores is not None and downed_cores != "None":
                ignored_cores = CoreSubsets()
                for downed_core in downed_cores.split(":"):
                    x, y, processor_id = downed_core.split(",")
                    ignored_cores.add_processor(int(x), int(y),
                                                int(processor_id))

            self._txrx = create_transceiver_from_hostname(
                hostname=hostname,
                discover=False,
                ignore_chips=ignored_chips,
                ignore_cores=ignored_cores)

            #do autoboot if possible
            machine_version = conf.config.get("Machine", "version")
            if machine_version is None:
                raise exceptions.ConfigurationException(
                    "Please set a machine version number in the configuration "
                    "file (pacman.cfg or pacman.cfg)")
            self._txrx.ensure_board_is_ready(int(machine_version))
            self._txrx.discover_scamp_connections()
            self._machine = self._txrx.get_machine_details()
        else:
            virtual_x_dimension = conf.config.getint("Machine",
                                                  "virutal_board_x_dimension")
            virtual_y_dimension = conf.config.getint("Machine",
                                                  "virutal_board_y_dimension")
            requires_wrap_around = conf.config.getboolean("Machine",
                                                   "requires_wrap_arounds")
            self._machine = VirtualMachine(
                x_dimension=virtual_x_dimension,
                y_dimension=virtual_y_dimension,
                with_wrap_arounds=requires_wrap_around)

    def _add_iptag(self, iptag):
        self._iptags.append(iptag)

    def _add_reverse_tag(self, reverse_iptag):
        self._reverse_iptags.append(reverse_iptag)

    def _load_iptags(self):
        for iptag in self._iptags:
            self._txrx.set_ip_tag(iptag)

    def _load_reverse_ip_tags(self):
        for reverse_iptag in self._reverse_iptags:
            self._txrx.set_reverse_ip_tag(reverse_iptag)

    def _retieve_provance_data_from_machine(
            self, executable_targets, routing_tables, machine):
        #create writer to a report in reports
        reports.generate_provance_routings(routing_tables, machine, self._txrx,
                                           self._report_default_directory)

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

    def host_based_data_specificiation_execution(self, hostname, placements,
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
                    associated_vertex.get_data_spec_file_path(
                        placement.x, placement.y, placement.p, hostname
                    )
                app_data_file_path = \
                    associated_vertex.get_application_data_file_path(
                        placement.x, placement.y, placement.p, hostname
                    )
                data_spec_reader = FileDataReader(data_spec_file_path)
                data_writer = FileDataWriter(app_data_file_path)

                #locate current memory requirement
                current_memory_available = SDRAM.DEFAULT_SDRAM_BYTES
                memory_tracker_key = (placement.x, placement.y)
                if memory_tracker_key in space_based_memory_tracker.keys():
                    current_memory_available = \
                        space_based_memory_tracker[memory_tracker_key]

                #generate a file writer for dse report (app pointer table)
                report_writer = None
                if conf.config.getboolean("Reports", "writeTextSpecs"):
                    new_report_directory = \
                        os.path.join(self._report_default_directory,
                                     "data_spec_text_files")

                    if not os.path.exists(new_report_directory):
                        os.mkdir(new_report_directory)

                    file_name = "{}_DSE_report_for_{}_{}_{}.txt"\
                                .format(hostname, placement.x, placement.y,
                                        placement.p)
                    report_file_path = os.path.join(new_report_directory,
                                                    file_name)
                    report_writer = FileDataWriter(report_file_path)

                #generate data spec executor
                host_based_data_spec_executor = DataSpecificationExecutor(
                    data_spec_reader, data_writer, current_memory_available,
                    report_writer)

                #update memory calc and run data spec executor
                bytes_used_by_spec, bytes_written_by_spec = \
                    host_based_data_spec_executor.execute()

                #update base address mapper
                processor_mapping_key = (placement.x, placement.y, placement.p)
                processor_to_app_data_base_address[processor_mapping_key] = \
                    {'start_address':
                        ((SDRAM.DEFAULT_SDRAM_BYTES - current_memory_available)
                         + constants.SDRAM_BASE_ADDR),
                     'memory_used': bytes_used_by_spec,
                     'memory_written': bytes_written_by_spec}

                space_based_memory_tracker[memory_tracker_key] = \
                    current_memory_available - bytes_used_by_spec

            #update the progress bar
            progress_bar.update()
        # close the progress bar
        progress_bar.end()
        return processor_to_app_data_base_address

    def _start_execution_on_machine(self, executable_targets, app_id, runtime,
                                    time_scaling, waiting_on_confirmation,
                                    database_thread, in_debug_mode):
        # deduce how many processors this application uses up
        total_processors = 0
        total_cores = list()
        executable_keys = executable_targets.keys()
        for executable_target in executable_keys:
            core_subsets = executable_targets[executable_target]
            for core_subset in core_subsets:
                for _ in core_subset.processor_ids:
                    total_processors += 1
                total_cores.append(core_subset)

        processor_c_main = self._txrx.get_core_state_count(app_id,
                                                           CPUState.C_MAIN)
        # check that everything has gone though c main to reach sync0 or
        # failing for some unknown reason
        while processor_c_main != 0:
            time.sleep(0.1)
            processor_c_main = self._txrx.get_core_state_count(app_id,
                                                               CPUState.C_MAIN)

        # check that the right number of processors are in sync0
        processors_ready = self._txrx.get_core_state_count(app_id,
                                                           CPUState.SYNC0)

        if processors_ready != total_processors:
            successful_cores, unsucessful_cores = \
                self._break_down_of_failure_to_reach_state(total_cores,
                                                           CPUState.SYNC0)
            # last chance to slip out of error check
            if len(successful_cores) != total_processors:
                # break_down the successful cores and unsuccessful cores into
                # string
                # reps
                break_down = \
                    self.turn_break_downs_into_string(
                        total_cores, successful_cores, unsucessful_cores,
                        CPUState.SYNC0)
                raise exceptions.ExecutableFailedToStartException(
                    "Only {} processors out of {} have sucessfully reached "
                    "sync0 with breakdown of: {}"
                    .format(processors_ready, total_processors, break_down))

        # wait till vis is ready for us to start if required
        if waiting_on_confirmation:
            logger.info("*** Awaiting for a response from the visualiser to "
                        "state its ready for the simulation to start ***")
            database_thread.wait_for_confirmation()

        # if correct, start applications
        logger.info("Starting application")
        self._txrx.send_signal(app_id, SCPSignal.SYNC0)

        # check all apps have gone into run state
        logger.info("Checking that the application has started")
        processors_running = self._txrx.get_core_state_count(app_id,
                                                             CPUState.RUNNING)
        processors_finished = self._txrx.get_core_state_count(app_id,
                                                              CPUState.FINSHED)
        if processors_running < total_processors:
            if processors_running + processors_finished >= total_processors:
                logger.warn("some processors finished between signal "
                            "transmissions. Could be a sign of an error")
            else:
                sucessful_cores, unsucessful_cores = \
                    self._break_down_of_failure_to_reach_state(total_cores,
                                                               CPUState.RUNNING)
                # break_down the successful cores and unsuccessful cores into
                # string reps
                break_down = self.turn_break_downs_into_string(
                    total_cores, sucessful_cores, unsucessful_cores,
                    CPUState.RUNNING)
                raise exceptions.ExecutableFailedToStartException(
                    "Only {} of {} processors started with breakdown {}"
                    .format(processors_running, total_processors, break_down))

        # if not running for infinity, check that applications stop correctly
        if runtime is not None:
            time_to_wait = ((runtime / 1000.0) * time_scaling) + 1.0
            logger.info("Application started - waiting {} seconds for it to"
                        " stop".format(time_to_wait))
            time.sleep(time_to_wait)
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
                    # break_down the successful cores and unsuccessful cores
                    # into string reps
                    break_down = self.turn_break_downs_into_string(
                        total_cores, sucessful_cores, unsucessful_cores,
                        CPUState.RUNNING)
                    raise exceptions.ExecutableFailedToStopException(
                        "{} cores have gone into a run time error state with "
                        "breakdown {}.".format(processors_rte, break_down))
                logger.info("Simulation still not finished or failed - "
                            "waiting a bit longer...")
                time.sleep(0.5)

            processors_exited =\
                self._txrx.get_core_state_count(app_id, CPUState.FINSHED)

            if processors_exited < total_processors:
                sucessful_cores, unsucessful_cores = \
                    self._break_down_of_failure_to_reach_state(
                        total_cores, CPUState.RUNNING)
                # break_down the successful cores and unsuccessful cores into
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

    def _break_down_of_failure_to_reach_state(self, total_cores, state):
        sucessful_cores = list()
        unsucessful_cores = dict()
        core_infos = self._txrx.get_cpu_information(total_cores)
        for core_info in core_infos:
            if core_info.state == state:
                sucessful_cores.append((core_info.x, core_info.y, core_info.p))
            else:
                unsucessful_cores[(core_info.x, core_info.y, core_info.p)] = \
                    core_info.state.name
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
                        .format(core_info.x, core_info.y, processor_id,
                                state.name, os.linesep)
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

    def _load_application_data(
            self, placements, router_tables, vertex_to_subvertex_mapper,
            processor_to_app_data_base_address, hostname, app_id):

        #if doing reload, start script
        if self._reports_states.transciever_report:
            reports.start_transceiver_rerun_script(
                conf.config.get("SpecGeneration", "Binary_folder"), hostname,
                conf.config.get("Machine", "version"))

        #go through the placements and see if theres any application data to
        # load

        progress_bar = ProgressBar(len(list(placements.placements)),
                                   "Loading application data onto the machine")
        for placement in placements.placements:
            associated_vertex = \
                vertex_to_subvertex_mapper.get_vertex_from_subvertex(
                    placement.subvertex)

            if isinstance(associated_vertex, AbstractDataSpecableVertex):
                logger.debug("loading application data for vertex {}"
                             .format(associated_vertex.label))
                key = (placement.x, placement.y, placement.p)
                start_address = \
                    processor_to_app_data_base_address[key]['start_address']
                memory_written = \
                    processor_to_app_data_base_address[key]['memory_written']
                file_path_for_application_data = \
                    associated_vertex.get_application_data_file_path(
                        placement.x, placement.y, placement.p, hostname)
                application_data_file_reader = \
                    SpinnmanFileDataReader(file_path_for_application_data)
                logger.debug("writing application data for vertex {}"
                             .format(associated_vertex.label))
                self._txrx.write_memory(placement.x, placement.y, start_address,
                                        application_data_file_reader,
                                        memory_written)
                #update user 0 so that it points to the start of the \
                # applications data region on sdram
                logger.debug("writing user 0 address for vertex {}"
                             .format(associated_vertex.label))
                user_o_register_address = \
                    self._txrx.get_user_0_register_address_from_core(
                        placement.x, placement.y, placement.p)
                self._txrx.write_memory(placement.x, placement.y,
                                        user_o_register_address, start_address)

                #add lines to rerun_script if requested
                if self._reports_states.transciever_report:
                    binary_folder = \
                        conf.config.get("SpecGeneration", "Binary_folder")
                    reports.re_load_script_application_data_load(
                        file_path_for_application_data, placement,
                        start_address, memory_written, user_o_register_address,
                        binary_folder)
            progress_bar.update()
        progress_bar.end()

        progress_bar = ProgressBar(len(list(router_tables.routing_tables)),
                                   "Loading routing data onto the machine")
        #load each router table thats needed for the application to run into
        # the chips sdram
        for router_table in router_tables.routing_tables:
            if len(router_table.multicast_routing_entries) > 0:
                self._txrx.load_multicast_routes(
                    router_table.x, router_table.y,
                    router_table.multicast_routing_entries, app_id=app_id)
                if self._reports_states.transciever_report:
                    binary_folder = conf.config.get("SpecGeneration",
                                                    "Binary_folder")
                    reports.re_load_script_load_routing_tables(
                        router_table, binary_folder, app_id)
            progress_bar.update()
        progress_bar.end()

    def _load_executable_images(self, executable_targets, app_id):
        """
        go through the exeuctable targets and load each binary to everywhere and
        then set each given core to sync0 that require it
        """
        if self._reports_states.transciever_report:
            binary_folder = os.path.join(conf.config.get("SpecGeneration",
                                                         "Binary_folder"))
            reports.re_load_script_load_executables_init(binary_folder,
                                                         executable_targets)

        progress_bar = ProgressBar(len(executable_targets.keys()),
                                   "Loading executables onto the machine")
        for exectuable_target_key in executable_targets.keys():
            file_reader = SpinnmanFileDataReader(exectuable_target_key)
            core_subset = executable_targets[exectuable_target_key]

            file_to_read_in = open(exectuable_target_key, 'rb')
            buf = file_to_read_in.read()
            size = (len(buf))

            self._txrx.execute_flood(core_subset, file_reader, app_id,
                                     size)

            if self._reports_states.transciever_report:
                binary_folder = os.path.join(conf.config.get("SpecGeneration",
                                                             "Binary_folder"))
                reports.re_load_script_load_executables_individual(
                    binary_folder, exectuable_target_key, app_id, size)
            progress_bar.update()
        progress_bar.end()
