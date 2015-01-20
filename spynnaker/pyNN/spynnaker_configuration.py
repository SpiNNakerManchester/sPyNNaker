from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.report_states import ReportState
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN import overridden_pacman_functions


from pacman.operations import partition_algorithms
from pacman.operations import placer_algorithms
from pacman.operations import router_algorithms
from pacman.operations import routing_info_allocator_algorithms


import os
import datetime
import shutil
import logging
import math

logger = logging.getLogger(__name__)


class SpynnakerConfiguration(object):

    def __init__(self, host_name, graph_label):
        #machine specific bits
        self._hostname = host_name
        self._time_scale_factor = None
        self._machine_time_step = None
        self._runtime = None

        #specific utility vertexes
        self._multi_cast_vertex = None
        self._txrx = None

        #debug flag
        self._in_debug_mode = None

        #main objects
        self._partitionable_graph = PartitionableGraph(label=graph_label)
        self._partitioned_graph = None
        self._graph_mapper = None
        self._no_machine_time_steps = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._pruner_infos = None
        self._has_ran = False
        self._reports_states = None
        self._app_id = None

        #pacman mapping objects
        self._partitioner_algorithm = None
        self._placer_algorithm = None
        self._key_allocator_algorithm = None
        self._router_algorithm = None
        self._report_default_directory = None
        self._app_data_runtime_folder = None
        self._this_run_time_string_repenstation = None

        #exeuctable params
        self._do_load = None
        self._do_run = None
        self._writeTextSpecs = None
        self._retrieve_provance_data = True

        #helper data stores
        self._current_max_tag_value = 0

        #database objects
        self._create_database = False
        self._database_thread = None

    def _set_up_output_application_data_specifics(self):
        where_to_write_application_data_files = \
            config.get("Reports", "defaultApplicationDataFilePath")
        created_folder = False
        this_run_time_folder = None
        if where_to_write_application_data_files == "DEFAULT":
            directory = os.getcwd()
            application_generated_data_file_folder = \
                os.path.join(directory, 'application_generated_data_files')
            if not os.path.exists(application_generated_data_file_folder):
                os.makedirs(application_generated_data_file_folder)
                created_folder = True

            if not created_folder:
                self._move_report_and_binary_files(
                    config.getint("Reports", "max_application_binaries_kept"),
                    application_generated_data_file_folder)

            #add time stamped folder for this run
            this_run_time_folder = \
                os.path.join(application_generated_data_file_folder, "latest")
            if not os.path.exists(this_run_time_folder):
                os.makedirs(this_run_time_folder)

            #store timestamp in latest/time_stamp
            time_of_run_file_name = os.path.join(this_run_time_folder,
                                                 "time_stamp")
            writer = open(time_of_run_file_name, "w")
            writer.writelines("app_{}_{}"
                              .format(self._app_id,
                                      self._this_run_time_string_repenstation))
            writer.flush()
            writer.close()

        elif where_to_write_application_data_files == "TEMP":
            pass  # just dont set the config param, code downstairs
            #  from here will create temp folders if needed
        else:
            this_run_time_folder = \
                os.path.join(where_to_write_application_data_files, "latest")
            if not os.path.exists(this_run_time_folder):
                os.makedirs(this_run_time_folder)
            else:
                self._move_report_and_binary_files(
                    config.getint("Reports", "max_application_binaries_kept"),
                    where_to_write_application_data_files)

            #store timestamp in latest/time_stamp
            time_of_run_file_name = os.path.join(this_run_time_folder,
                                                 "time_stamp")
            writer = open(time_of_run_file_name, "w")
            writer.writelines("app_{}_{}"
                              .format(self._app_id,
                                      self._this_run_time_string_repenstation))

            if not os.path.exists(this_run_time_folder):
                os.makedirs(this_run_time_folder)
        if not config.has_section("SpecGeneration"):
            config.add_section("SpecGeneration")
            config.set("SpecGeneration", "Binary_folder", this_run_time_folder)
            self._app_data_runtime_folder = this_run_time_folder

    def _set_up_report_specifics(self):
        self._writeTextSpecs = False
        if config.getboolean("Reports", "reportsEnabled"):
            self._writeTextSpecs = config.getboolean("Reports",
                                                     "writeTextSpecs")
        #determine common report folder
        config_param = config.get("Reports", "defaultReportFilePath")
        created_folder = False
        if config_param == "DEFAULT":
            directory = os.getcwd()

            #global reports folder
            self._report_default_directory = os.path.join(directory, 'reports')
            if not os.path.exists(self._report_default_directory):
                os.makedirs(self._report_default_directory)
                created_folder = True
        elif config_param == "REPORTS":
            self._report_default_directory = 'reports'
            if not os.path.exists(self._report_default_directory):
                os.makedirs(self._report_default_directory)
        else:
            self._report_default_directory = \
                os.path.join(config_param, 'reports')
            if not os.path.exists(self._report_default_directory):
                os.makedirs(self._report_default_directory)

        #clear and clean out folders considered not useful anymore
        if not created_folder \
                and len(os.listdir(self._report_default_directory)) > 0:
            self._move_report_and_binary_files(
                config.getint("Reports", "max_reports_kept"),
                self._report_default_directory)

        #handle timing app folder and cleaning of report folder from last run
        app_folder_name = os.path.join(self._report_default_directory, "latest")
        if not os.path.exists(app_folder_name):
                os.makedirs(app_folder_name)
        #store timestamp in latest/time_stamp
        time_of_run_file_name = os.path.join(app_folder_name, "time_stamp")
        writer = open(time_of_run_file_name, "w")

        # determine the time slot for later
        this_run_time = datetime.datetime.now()
        self._this_run_time_string_repenstation = \
            str(this_run_time.date()) + "-" + str(this_run_time.hour) + "-" + \
            str(this_run_time.minute) + "-" + str(this_run_time.second)
        writer.writelines("app_{}_{}"
                          .format(self._app_id,
                                  self._this_run_time_string_repenstation))
        writer.flush()
        writer.close()
        self._report_default_directory = app_folder_name
        self._retrieve_provance_data = config.getboolean("Reports",
                                                         "writeProvanceData")

    def _set_up_main_objects(self):
        self._in_debug_mode = conf.config.get("Mode", "mode") == "Debug"
        #report object
        if config.getboolean("Reports", "reportsEnabled"):
            self._reports_states = ReportState()
        self._create_database = \
            config.getboolean("Database", "create_database")

        #communication objects
        self._iptags = list()
        self._app_id = config.getint("Machine", "appID")


    def _set_up_executable_specifics(self):
        #loading and running config params
        self._do_load = True
        if config.has_option("Execute", "load"):
            self._do_load = config.getboolean("Execute", "load")

        self._do_run = True
        if config.has_option("Execute", "run"):
            self._do_run = config.getboolean("Execute", "run")

    def _set_up_pacman_algorthms_listings(self):
         #algorithum lists
        partitioner_algorithms_list = \
            conf.get_valid_components(partition_algorithms, "Partitioner")
        self._partitioner_algorithm = \
            partitioner_algorithms_list[config.get("Partitioner", "algorithm")]

        placer_algorithms_list = \
            conf.get_valid_components(placer_algorithms, "Placer")
        self._placer_algorithm = \
            placer_algorithms_list[config.get("Placer", "algorithm")]

        #get common key allocator algorithms
        key_allocator_algorithms_list = \
            conf.get_valid_components(routing_info_allocator_algorithms,
                                      "RoutingInfoAllocator")
        #get pynn specific key allocator
        pynn_overloaded_allocator = \
            conf.get_valid_components(overridden_pacman_functions,
                                      "RoutingInfoAllocator")
        key_allocator_algorithms_list.update(pynn_overloaded_allocator)

        self._key_allocator_algorithm = \
            key_allocator_algorithms_list[config.get("KeyAllocator",
                                                     "algorithm")]

        routing_algorithms_list = \
            conf.get_valid_components(router_algorithms, "Routing")
        self._router_algorithm = \
            routing_algorithms_list[config.get("Routing", "algorithm")]

    def _set_up_machine_specifics(self, timestep, min_delay, max_delay,
                                  hostname):
        self._machine_time_step = config.getint("Machine", "machineTimeStep")
        #deal with params allowed via the setup optimals
        if timestep is not None:
            timestep *= 1000  # convert into ms from microseconds
            config.set("Machine", "machineTimeStep", timestep)
            self._machine_time_step = timestep

        if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step".format(1.0 * timestep))

        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS
        delay_extention_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS \
            * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extention_max_supported_delay

        if max_delay is not None\
           and float(max_delay * 1000) > max_delay_tics_supported * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
            if not config.has_section("Model"):
                config.add_section("Model")
            config.set("Model", "min_delay", (min_delay * 1000) / timestep)

        if max_delay is not None:
            if not config.has_section("Model"):
                config.add_section("Model")
            config.set("Model", "max_delay", (max_delay * 1000) / timestep)

        if (config.has_option("Machine", "timeScaleFactor")
                and config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = \
                config.getint("Machine", "timeScaleFactor")
            if timestep * self._time_scale_factor < 1000:
                logger.warn("the combination of machine time step and the "
                            "machine time scale factor results in a real timer "
                            "tic that is currently not reliably supported by "
                            "the spinnaker machine.")
        else:
            self._time_scale_factor = max(1,
                                          math.ceil(1000.0 / float(timestep)))
            if self._time_scale_factor > 1:
                logger.warn("A timestep was entered that has forced pacman103 "
                            "to automatically slow the simulation down from "
                            "real time by a factor of {}. To remove this "
                            "automatic behaviour, please enter a "
                            "timescaleFactor value in your .pacman.cfg"
                            .format(self._time_scale_factor))
        if hostname is not None:
            self._hostname = hostname
            logger.warn("The machine name from PYNN setup is overriding the "
                        "machine name defined in the pacman.cfg file")
        elif config.has_option("Machine", "machineName"):
            self._hostname = config.get("Machine", "machineName")
        else:
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")
        use_virtual_board = config.getboolean("Machine", "virtual_board")
        if self._hostname == 'None' and not use_virtual_board:
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")

    @staticmethod
    def _move_report_and_binary_files(max_to_keep, starting_directory):
        app_folder_name = os.path.join(starting_directory, "latest")
        app_name_file = os.path.join(app_folder_name, "time_stamp")
        if os.path.isfile(app_name_file):
            time_stamp_in = open(app_name_file, "r")
            time_stamp_in_string = time_stamp_in.readline()
            time_stamp_in.close()
            os.remove(app_name_file)
            new_app_folder = os.path.join(starting_directory,
                                          time_stamp_in_string)
            extra = 2
            while os.path.exists(new_app_folder):
                new_app_folder = os.path.join(
                    starting_directory,
                    time_stamp_in_string + "_" + str(extra))
                extra += 1

            os.makedirs(new_app_folder)
            list_of_files = os.listdir(app_folder_name)
            for file_to_move in list_of_files:
                file_path = os.path.join(app_folder_name, file_to_move)
                shutil.move(file_path, new_app_folder)
            files_in_report_folder = os.listdir(starting_directory)
            # while theres more than the valid max, remove the oldest one
            while len(files_in_report_folder) > max_to_keep:
                files_in_report_folder.sort(
                    cmp, key=lambda temp_file:
                    os.path.getmtime(os.path.join(starting_directory,
                                                  temp_file)))
                oldest_file = files_in_report_folder[0]
                shutil.rmtree(os.path.join(starting_directory, oldest_file),
                              ignore_errors=True)
                files_in_report_folder.remove(oldest_file)
