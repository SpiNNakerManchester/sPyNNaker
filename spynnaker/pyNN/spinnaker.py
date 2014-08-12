#pacman imports
from pacman.model.constraints.vertex_requires_virtual_chip_in_machine_constraint import \
    VertexRequiresVirtualChipInMachineConstraint
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.operations import partition_algorithms
from pacman.operations import placer_algorithms
from pacman.operations import router_algorithms
from pacman.operations import routing_info_allocator_algorithms
from pacman.operations.partitioner import Partitioner
from pacman.operations.placer import Placer
from pacman.operations.routing_info_allocator import RoutingInfoAllocator
from pacman.operations.router import Router
from pacman.utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as pacman_utility_calls


#spinnmachine imports
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router as MachineRouter
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.chip import Chip


#internal imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.utility_models.multicastsource import MultiCastSource
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.report_states import ReportState
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.utility_models.live_spike_recorder\
    import LiveSpikeRecorder
from spynnaker.pyNN.visualiser_package.visualiser_creation_utility \
    import VisualiserCreationUtility
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN import overridden_pacman_functions
from spynnaker.pyNN.overridden_pacman_functions.subgraph_subedge_pruning import \
    SubgraphSubedgePruning
from spynnaker.pyNN import reports

#spinnman inports
from spinnman.transceiver import create_transceiver_from_hostname
from spinnman.model.iptag import IPTag
from spinnman.messages.scp.scp_signal import SCPSignal
from spinnman.data.file_data_reader import FileDataReader \
    as SpinnmanFileDataReader
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset
from spinnman.model.cpu_state import CPUState
from spinnman import reports as spinnman_reports


#data spec import
from data_specification.file_data_reader import FileDataReader \
    as DataSpecFileDataReader
from data_specification.file_data_writer import FileDataWriter
from data_specification.data_specification_executor\
    import DataSpecificationExecutor

import logging
import math
import time
import os
import sys
import datetime
import shutil
import pickle
import ntpath

logger = logging.getLogger(__name__)


class Spinnaker(object):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None):

        #machine specific bits
        self._hostname = host_name
        self._time_scale_factor = None
        self._machine_time_step = None

        #specific utility vertexes
        self._live_spike_recorder = None
        self._multi_cast_vertex = None
        self._txrx = None

        #visualiser objects
        self._visualiser = None
        self._wait_for_run = False
        self._visualiser_port = None
        self._visualiser_vertices = None
        self._visualiser_vertex_to_page_mapping = None
        self._visualiser_creation_utility = VisualiserCreationUtility()

        #main objects
        self._partitionable_graph = PartitionableGraph(label=graph_label)
        self._partitioned_graph = None
        self._graph_mapper = None
        self._machine = None
        self._no_machine_time_steps = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._pruner_infos = None
        self._runtime = None
        self._has_ran = False
        self._reports_states = None
        self._iptags = None
        self._app_id = None

        #pacman mapping objects
        self._partitioner_algorithm = None
        self._placer_algorithm = None
        self._key_allocator_algorithm = None
        self._routing_algorithm = None
        self._report_default_directory = None
        self.this_run_time_string_repenstation = None
        self._writeTextSpecs = None

        #exeuctable params
        self._do_load = None
        self._do_run = None
        if self._app_id is None:
            self._set_up_main_objects()
            self._set_up_pacman_algorthms_listings()
            self._set_up_executable_specifics()
            self._set_up_recording_specifics()
            self._set_up_report_specifics()
        self._set_up_output_application_data_specifics()
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)
    
        #get the machien time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))
        self._edge_count = 0

    def _set_up_output_application_data_specifics(self):
        where_to_write_application_data_files = \
            conf.config.get("Reports", "defaultApplicationDataFilePath")
        created_folder = False
        if where_to_write_application_data_files == "DEFAULT":
            exceptions_path = \
                os.path.abspath(exceptions.__file__)
            directory = \
                os.path.abspath(os.path.join(exceptions_path,
                                             os.pardir, os.pardir, os.pardir))
            #global folder
            application_generated_data_file_folder = \
                os.path.join(directory, 'application_generated_data_files')
            if not os.path.exists(application_generated_data_file_folder):
                os.makedirs(application_generated_data_file_folder)
                created_folder = True

            if not created_folder:
                self._move_report_and_binary_files(
                    conf.config.getint("Reports",
                                       "max_application_binaries_kept"),
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
                                      self.this_run_time_string_repenstation))
            writer.flush()
            writer.close()

            if not conf.config.has_section("SpecGeneration"):
                conf.config.add_section("SpecGeneration")
            conf.config.set("SpecGeneration", "Binary_folder",
                            this_run_time_folder)
        elif where_to_write_application_data_files == "TEMP":
            pass  # just dont set the config param, code downstairs
            #  from here will create temp folders if needed
        else:
            #add time stamped folder for this run
            this_run_time_folder = \
                os.path.join(where_to_write_application_data_files,
                             self.this_run_time_string_repenstation)
            if not os.path.exists(this_run_time_folder):
                os.makedirs(this_run_time_folder)
            conf.config.add_section("SpecGeneration")
            conf.config.set("SpecGeneration", "Binary_folder",
                            this_run_time_folder)

    def _set_up_report_specifics(self):
        self._writeTextSpecs = False
        if conf.config.getboolean("Reports", "reportsEnabled"):
            self._writeTextSpecs = conf.config.getboolean("Reports",
                                                          "writeTextSpecs")
        #determine common report folder
        config_param = conf.config.get("Reports", "defaultReportFilePath")
        created_folder = False
        if config_param == "DEFAULT":
            exceptions_path = \
                os.path.abspath(exceptions.__file__)
            directory = \
                os.path.abspath(os.path.join(exceptions_path,
                                             os.pardir, os.pardir, os.pardir))

            #global reports folder
            self._report_default_directory = os.path.join(directory, 'reports')
            if not os.path.exists(self._report_default_directory):
                os.makedirs(self._report_default_directory)
                created_folder = True
        else:
            self._report_default_directory = \
                os.path.join(config_param, 'reports')
            if not os.path.exists(self._report_default_directory):
                os.makedirs(self._report_default_directory)

        #clear and clean out folders considered not useful anymore
        if not created_folder:
            self._move_report_and_binary_files(
                conf.config.getint("Reports", "max_reports_kept"),
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
        self.this_run_time_string_repenstation = \
            str(this_run_time.date()) + "-" + str(this_run_time.hour) + "-" + \
            str(this_run_time.minute) + "-" + str(this_run_time.second)
        writer.writelines("app_{}_{}"
                          .format(self._app_id,
                                  self.this_run_time_string_repenstation))
        writer.flush()
        writer.close()
        self._report_default_directory = app_folder_name

    @staticmethod
    def _move_report_and_binary_files(max_to_keep, starting_directory):
        app_folder_name = os.path.join(starting_directory, "latest")
        app_name_file = os.path.join(app_folder_name, "time_stamp")
        time_stamp_in = open(app_name_file, "r")
        time_stamp_in_string = time_stamp_in.readline()
        time_stamp_in.close()
        new_app_folder = os.path.join(starting_directory, time_stamp_in_string)
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
                os.path.getmtime(os.path.join(starting_directory, temp_file)))
            oldest_file = files_in_report_folder[0]
            shutil.rmtree(os.path.join(starting_directory, oldest_file))
            files_in_report_folder.remove(oldest_file)

    def _set_up_recording_specifics(self):
        if conf.config.has_option("Recording", "send_live_spikes"):
            if conf.config.getboolean("Recording", "send_live_spikes"):
                port = None
                if conf.config.has_option("Recording", "live_spike_port"):
                    port = conf.config.getint("Recording", "live_spike_port")
                hostname = "localhost"
                if conf.config.has_option("Recording", "live_spike_host"):
                    hostname = conf.config.get("Recording", "live_spike_host")
                tag = None
                if conf.config.has_option("Recording", "live_spike_tag"):
                    tag = conf.config.getint("Recording", "live_spike_tag")
                if tag is None:
                    raise exceptions.ConfigurationException(
                        "Target tag for live spikes has not been set")

                # Set up the forwarding so that monitored spikes are sent to the
                # requested location
                self._set_tag_output(tag, port, hostname)
                #takes the same port for the visualiser if being used
                if conf.config.getboolean("Visualiser", "enable") and \
                   conf.config.getboolean("Machine", "have_board"):
                    self._visualiser_creation_utility.set_visulaiser_port(port)

    def _set_up_main_objects(self):
        #report object
        if conf.config.getboolean("Reports", "reportsEnabled"):
            self._reports_states = ReportState()

        #communication objects
        self._iptags = list()
        self._app_id = conf.config.getint("Machine", "appID")

    def _set_up_executable_specifics(self):
        #loading and running config params
        self._do_load = True
        if conf.config.has_option("Execute", "load"):
            self._do_load = conf.config.getboolean("Execute", "load")

        self._do_run = True
        if conf.config.has_option("Execute", "run"):
            self._do_run = conf.config.getboolean("Execute", "run")

        #sort out the executable folder location
        binary_path = os.path.abspath(exceptions.__file__)
        binary_path = os.path.abspath(os.path.join(binary_path, os.pardir))
        binary_path = os.path.join(binary_path, "model_binaries")

        if not conf.config.has_section("SpecGeneration"):
            conf.config.add_section("SpecGeneration")
        conf.config.set("SpecGeneration", "common_binary_folder", binary_path)

    def _set_up_pacman_algorthms_listings(self):
         #algorithum lists
        partitioner_algorithms_list = \
            conf.get_valid_components(partition_algorithms, "Partitioner")
        self._partitioner_algorithm = \
            partitioner_algorithms_list[conf.config.get("Partitioner",
                                                        "algorithm")]

        placer_algorithms_list = \
            conf.get_valid_components(placer_algorithms, "Placer")
        self._placer_algorithm = \
            placer_algorithms_list[conf.config.get("Placer", "algorithm")]

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
            key_allocator_algorithms_list[conf.config.get("KeyAllocator",
                                                          "algorithm")]

        routing_algorithms_list = \
            conf.get_valid_components(router_algorithms, "Routing")
        self._routing_algorithm = \
            routing_algorithms_list[conf.config.get("Routing", "algorithm")]

    def _set_up_machine_specifics(self, timestep, min_delay, max_delay,
                                  hostname):
        self._machine_time_step = conf.config.getint("Machine",
                                                     "machineTimeStep")
        #deal with params allowed via the setup optimals
        if timestep is not None:
            timestep *= 1000  # convert into ms from microseconds
            conf.config.set("Machine", "machineTimeStep", timestep)
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
            if not conf.config.has_section("Model"):
                conf.config.add_section("Model")
            conf.config.set("Model", "min_delay", (min_delay * 1000) / timestep)

        if max_delay is not None:
            if not conf.config.has_section("Model"):
                conf.config.add_section("Model")
            conf.config.set("Model", "max_delay", (max_delay * 1000) / timestep)

        if (conf.config.has_option("Machine", "timeScaleFactor")
                and conf.config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = conf.config.getint("Machine",
                                                         "timeScaleFactor")
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
        elif conf.config.has_option("Machine", "machineName"):
            self._hostname = conf.config.get("Machine", "machineName")
        else:
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")
        if self._hostname == 'None':
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")

    def run(self, run_time):
        self._setup_interfaces()

        if self._reports_states is not None:
            reports.network_specification_report(self._report_default_directory,
                                                 self._partitionable_graph, self._hostname)

        #calcualte number of machien time steps
        if run_time is not None:
            self._no_machine_time_steps =\
                int((run_time * 1000.0) / self._machine_time_step)
            ceiled_machine_time_steps = \
                math.ceil((run_time * 1000.0) / self._machine_time_step)
            if self._no_machine_time_steps != ceiled_machine_time_steps:
                raise exceptions.ConfigurationException(
                    "The runtime and machine time step combination result in "
                    "a factional number of machine runable time steps and "
                    "therefore spinnaker cannot determine how many to run for")
        else:
            self._no_machine_time_steps = None
            logger.warn("You have set a runtime that will never end, this may"
                        "cause the neural models to fail to partition "
                        "correctly")

        do_timing = conf.config.getboolean("Reports", "outputTimesForSections")
        if do_timing:
            timer = Timer()
        else:
            timer = None

        #update models with new no_machine_time_step
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractDataSpecableVertex):
                vertex.set_application_runtime(self._runtime)
                vertex.set_no_machine_time_steps(self._no_machine_time_steps)
            if isinstance(vertex, AbstractRecordableVertex) and not \
                    isinstance(vertex, AbstractDataSpecableVertex):
                vertex.set_no_machine_time_step(self._no_machine_time_steps)

        self.set_runtime(run_time)
        logger.info("*** Running Mapper *** ")
        if do_timing:
            timer.start_timing()
        self.map_model()
        if do_timing:
            timer.take_sample()

        #execute data spec generation
        if do_timing:
            timer.start_timing()
        logger.info("*** Generating Output *** ")
        logger.debug("")
        executable_targets = self.generate_data_specifications()
        if do_timing:
            timer.take_sample()

        #execute data spec execution
        if do_timing:
            timer.start_timing()
        processor_to_app_data_base_address = \
            self.execute_data_specification_execution(
                conf.config.getboolean("SpecExecution", "specExecOnHost"),
                self._hostname)

        #engage vis if requested
        if do_timing:
            timer.take_sample()
        if conf.config.getboolean("Visualiser", "enable"):
            self.start_visualiser()

        if conf.config.getboolean("Execute", "run_simulation"):
            if do_timing:
                timer.start_timing()

            if self._do_load is True:
                logger.info("*** Loading data ***")
                self._load_application_data(self._placements,
                                            self._graph_mapper,
                                            processor_to_app_data_base_address)
                logger.info("*** Loading executables ***")
                self._load_executable_images(executable_targets)
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                self._start_execution_on_machine(executable_targets)
                self._has_ran = True
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _setup_interfaces(self):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        has_board = conf.config.getboolean("Machine", "have_board")
        requires_visualiser = conf.config.getboolean("Visualiser", "enable")

        if has_board:
            if self._reports_states is None:
                self._txrx = create_transceiver_from_hostname(
                    hostname=self._hostname, generate_reports=False,
                    discover=False)
            else:
                self._txrx = create_transceiver_from_hostname(
                    hostname=self._hostname, generate_reports=True,
                    default_report_directory=self._report_default_directory,
                    discover=False)
            #do autoboot if possible
            self._txrx.ensure_board_is_ready(int(conf.config.get("Machine",
                                                                 "version")))
            self._txrx.discover_connections()
        self._machine = self._txrx.get_machine_details()

        if requires_visualiser:
            self._visualiser, self._visualiser_vertex_to_page_mapping = \
                self._visualiser_creation_utility.create_visualiser_interface(
                    has_board, self._txrx, self._partitionable_graph,
                    self._visualiser_vertices, self._machine, self._partitioned_graph,
                    self._placements, self._router_tables, self._runtime,
                    self._machine_time_step)

    @property
    def app_id(self):
        return self._app_id

    @property
    def has_ran(self):
        return self._has_ran

    @property
    def machine_time_step(self):
        return self._machine_time_step

    @property
    def get_multi_cast_source(self):
        return self._multi_cast_vertex

    @property
    def sub_graph(self):
        return self._partitioned_graph

    @property
    def partitionable_graph(self):
        return self._partitionable_graph

    def set_app_id(self, value):
        self._app_id = value

    def set_runtime(self, value):
        self._runtime = value

    def map_model(self):
        """
        executes the pacman compilation stack
        """
        pacman_report_state = \
            self._reports_states.generate_pacman_report_states()

        self._check_if_theres_any_pre_placement_constraints_to_satisify()
        
        #execute partitioner
        partitioner = Partitioner(
            partition_algorithm=self._partitioner_algorithm,
            machine_time_step=self._machine_time_step,
            no_machine_time_steps=self._no_machine_time_steps,
            report_folder=self._report_default_directory,
            report_states=pacman_report_state, hostname=self._hostname,
            placer_algorithm=self._placer_algorithm, machine=self._machine)
        self._partitioned_graph, self._graph_mapper = \
            partitioner.run(self._partitionable_graph)

        #execute placer
        placer = Placer(
            machine=self._machine, report_states=pacman_report_state,
            report_folder=self._report_default_directory,
            partitonable_graph=self._partitionable_graph,
            hostname=self._hostname, placer_algorithm=self._placer_algorithm)
        self._placements = \
            placer.run(self._partitioned_graph, self._graph_mapper)

        #execute pynn subedge pruning
        pruner = SubgraphSubedgePruning()
        self._partitioned_graph, self._graph_mapper = \
            pruner.run(self._partitioned_graph, self._graph_mapper)

        #execute key allocator
        key_allocator = RoutingInfoAllocator(
            report_states=pacman_report_state, hostname=self._hostname,
            report_folder=self._report_default_directory, machine=self._machine,
            graph_mapper=self._graph_mapper,
            routing_info_allocator_algorithm=self._key_allocator_algorithm)
        self._routing_infos = key_allocator.run(self._partitioned_graph,
                                                self._placements)

        #execute router
        router = Router(report_folder=self._report_default_directory,
                        report_states=self._reports_states,
                        partitionable_graph=self._partitionable_graph,
                        graph_mappings=self._graph_mapper)
        self._router_tables = router.run(
            self._routing_infos, self._placements, self._machine,
            self._partitioned_graph)

    def generate_data_specifications(self):
        #iterate though subvertexes and call generate_data_spec for each vertex
        executable_targets = dict()

        #create a progress bar for end users
        progress_bar = ProgressBar(len(list(self._placements.placements)),
                                   "on generating data specifications")

        for placement in self._placements.placements:
            associated_vertex =\
                self._graph_mapper.get_vertex_from_subvertex(
                    placement.subvertex)
            # if the vertex can generate a DSG, call it
            subclass_list = \
                pacman_utility_calls.\
                locate_all_subclasses_of(AbstractDataSpecableVertex)
            if type(associated_vertex) in subclass_list:
                associated_vertex.generate_data_spec(
                    placement.x, placement.y, placement.p, placement.subvertex,
                    self._partitioned_graph, self._partitionable_graph,
                    self._routing_infos, self._hostname, self._graph_mapper)

                binary_name = associated_vertex.get_binary_file_name()
                if binary_name in executable_targets.keys():
                    executable_targets[binary_name].add_processor(placement.x,
                                                                  placement.y,
                                                                  placement.p)
                else:
                    processors = [placement.p]
                    initial_core_subset = CoreSubset(placement.x, placement.y,
                                                     processors)
                    list_of_core_subsets = [initial_core_subset]
                    executable_targets[binary_name] = \
                        CoreSubsets(list_of_core_subsets)
            #update the progress bar
            progress_bar.update()
        #finish the progress bar
        progress_bar.end()
        return executable_targets

    def execute_data_specification_execution(self, host_based_execution,
                                             hostname):
        if host_based_execution:
            return self.host_based_data_specificiation_execution(hostname)
        else:
            return self._chip_based_data_specificiation_execution(hostname)

    def _chip_based_data_specificiation_execution(self, hostname):
        raise NotImplementedError

    def host_based_data_specificiation_execution(self, hostname):
        space_based_memory_tracker = dict()
        processor_to_app_data_base_address = dict()
         #create a progress bar for end users
        progress_bar = ProgressBar(len(list(self._placements.placements)),
                                   "on executing data specifications on the "
                                   "host machine")

        for placement in self._placements.placements:
            associated_vertex = self._graph_mapper.\
                get_vertex_from_subvertex(placement.subvertex)
            # if the vertex can generate a DSG, call it
            subclass_list = pacman_utility_calls.\
                locate_all_subclasses_of(AbstractDataSpecableVertex)
            if associated_vertex in subclass_list:
                data_spec_file_path = \
                    associated_vertex.get_data_spec_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                app_data_file_path = \
                    associated_vertex.get_application_data_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                data_spec_reader = DataSpecFileDataReader(data_spec_file_path)
                data_writer = FileDataWriter(app_data_file_path)

                #locate current memory requirement
                current_memory_avilable = SDRAM.DEFAULT_SDRAM_BYTES
                key = "{}:{}".format(placement.x, placement.y)
                if key in space_based_memory_tracker.keys():
                    current_memory_avilable = space_based_memory_tracker[key]

                #generate data spec exeuctor
                host_based_data_spec_exeuctor = DataSpecificationExecutor(
                    data_spec_reader, data_writer,
                    SDRAM.DEFAULT_SDRAM_BYTES - current_memory_avilable)

                #update memory calc and run data spec executor
                bytes_used_by_spec = host_based_data_spec_exeuctor.execute()

                #update base address mapper
                key = "{}:{}:{}".format(placement.x, placement.y, placement.p)
                processor_to_app_data_base_address[key] = \
                    {'start_address':
                        ((SDRAM.DEFAULT_SDRAM_BYTES - current_memory_avilable)
                         + constants.SDRAM_BASE_ADDR),
                     'memory_used': bytes_used_by_spec}

                if key in space_based_memory_tracker.keys():
                    space_based_memory_tracker[key] = \
                        current_memory_avilable + bytes_used_by_spec
                else:
                    space_based_memory_tracker[key] = bytes_used_by_spec
            #update the progress bar
            progress_bar.update()
        #close the progress bar
        progress_bar.end()
        return processor_to_app_data_base_address

    def start_visualiser(self):
        """starts the port listener and ties it to the visualiser pages as
         required
        """
       #register a listener at the trasnciever for each visualised vertex
        for vertex in self._visualiser_vertices:
            associated_page = self._visualiser_vertex_to_page_mapping[vertex]
            if associated_page is not None:
                self._txrx.register_listener(associated_page.recieved_spike(),
                                             self._hostname)
        self._visualiser.start()

    def stop(self):
        self._txrx.send_signal(self._app_id, SCPSignal.STOP)
        if conf.config.getboolean("Visualiser", "enable"):
            self._visualiser.stop()

    def _start_execution_on_machine(self, executable_targets):
        #deduce how many processors this application uses up
        total_processors = 0
        executable_keys = executable_targets.keys()
        for executable_target in executable_keys:
            core_subset = executable_targets[executable_target]
            for _ in core_subset:
                total_processors += 1

        #check that the right number of processors are in sync0
        processors_ready = self._txrx.get_core_state_count(self._app_id,
                                                           CPUState.SYNC0)

        if processors_ready != total_processors:
            raise exceptions.ExecutableFailedToStartException(
                "Only {} processors out of {} have sucessfully reached sync0"
                .format(processors_ready, total_processors))

        # if correct, start applications
        logger.info("Starting application")
        self._txrx.send_signal(self._app_id, SCPSignal.SYNC0)

        #check all apps have gone into run state
        logger.info("Checking that the application has started")
        processors_running = self._txrx.get_core_state_count(self._app_id,
                                                             CPUState.RUNNING)
        if processors_running < total_processors:
            raise exceptions.ExecutableFailedToStartException(
                "Only {} of {} processors started".format(processors_running,
                                                          total_processors))

        #if not running for infinity, check that applications stop correctly
        if self._runtime is not None:
            logger.info("Application started - waiting for it to stop")
            time.sleep(self._runtime / 1000.0)
            processors_not_finished = processors_ready
            while processors_not_finished != 0:
                processors_not_finished = \
                    self._txrx.get_core_state_count(self._app_id,
                                                    CPUState.RUNNING)
                processors_rte = \
                    self._txrx.get_core_state_count(self._app_id,
                                                    CPUState.RUN_TIME_EXCEPTION)
                if processors_rte > 0:
                    raise exceptions.ExecutableFailedToStopException(
                        "{} cores have gone into a run time error state."
                        .format(processors_rte))

            processors_exited =\
                self._txrx.get_core_state_count(self._app_id, CPUState.FINSHED)

            if processors_exited < total_processors:
                raise exceptions.ExecutableFailedToStopException(
                    "{} of the processors failed to exit successfully"
                    .format(total_processors - processors_exited)
                )

            logger.info("Application has run to completion")
        else:
            logger.info("Application is set to run forever - PACMAN is exiting")

        if self._reports_states.transciever_report:
            commands = list()
            commands.append("txrx.get_core_state_count({}, CPUState.SYNC0)"
                            .format(self._app_id))
            commands.append("txrx.send_signal({}, SCPSignal.SYNC0"
                            .format(self._app_id))
            spinnman_reports.append_to_rerun_script(
                conf.config.get("SpecGeneration", "Binary_folder"),
                commands)

    def _set_tag_output(self, tag, port, hostname):
        self._iptags.append(IPTag(tag=tag, port=port, address=hostname))

    def add_vertex(self, vertex_to_add):
        if type(vertex_to_add) == type(MultiCastSource(self._machine_time_step)):
            self._multi_cast_vertex = vertex_to_add
        self._partitionable_graph.add_vertex(vertex_to_add)

    def add_edge(self, edge_to_add):
        self._partitionable_graph.add_edge(edge_to_add)

    def create_population(self, size, cellclass, cellparams, structure, label):
        return Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self,
            multi_cast_vertex=self._multi_cast_vertex)

    def create_projection(self, presynaptic_population, postsynaptic_population,
                          connector, source, target, synapse_dynamics, label,
                          rng):
        if label is None:
            label = "Projection {}".format(self._edge_count)
            self._edge_count += 1
        return Projection(
            presynaptic_population=presynaptic_population, label=label,
            postsynaptic_population=postsynaptic_population, rng=rng,
            connector=connector, source=source, target=target,
            synapse_dynamics=synapse_dynamics, spinnaker_control=self,
            machine_time_step=self._machine_time_step)

    def add_edge_to_recorder_vertex(self, vertex_to_record_from):
        #check to see if it needs to be created in the frist place
        if self._live_spike_recorder is None:
            self._live_spike_recorder = \
                LiveSpikeRecorder(self.machine_time_step)
            self.add_vertex(self._live_spike_recorder)
        #create the edge and add
        edge = PartitionableEdge(vertex_to_record_from,
                                 self._live_spike_recorder, "recorder_edge")
        self.add_edge(edge)

    def add_visualiser_vertex(self, visualiser_vertex_to_add):
        if self._visualiser_vertices is None:
            self._visualiser_vertices = list()
        self._visualiser_vertices.append(visualiser_vertex_to_add)

    def _load_application_data(self, placements, vertex_to_subvertex_mapper,
                               processor_to_app_data_base_address):

        #if doing reload, start script
        if self._reports_states.transciever_report:
            spinnman_reports.start_transceiver_rerun_script(
                conf.config.get("SpecGeneration", "Binary_folder"),
                self._hostname)

        #go through the placements and see if theres any application data to
        # load
        for placement in placements.placements:
            associated_vertex = \
                vertex_to_subvertex_mapper.get_vertex_from_subvertex(
                    placement.subvertex)

            subclass_list = pacman_utility_calls.\
                locate_all_subclasses_of(AbstractDataSpecableVertex)
            if associated_vertex in subclass_list:
                key = "{}:{}:{}".format(placement.x, placement.y, placement.p)
                start_address = \
                    processor_to_app_data_base_address[key]['start_address']
                memory_used = \
                    processor_to_app_data_base_address[key]['memory_used']
                file_path_for_application_data = \
                    associated_vertex.get_application_data_file_name(
                        placement.x, placement.y, placement.p, self._hostname)
                application_data_file_reader = \
                    SpinnmanFileDataReader(file_path_for_application_data)
                self._txrx.write_memory(placement.x, placement.y, start_address,
                                        application_data_file_reader,
                                        memory_used)

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

    def _load_executable_images(self, executable_targets):
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

            self._txrx.execute_flood(core_subset, file_reader, self._app_id,
                                     size)

            if self._reports_states.transciever_report:
                lines = list()
                lines.append("core_subset = executable_targets[\"{}\"]"
                             .format(exectuable_target_key))
                lines.append("file_reader = SpinnmanFileDataReader(\"{}\")"
                             .format(exectuable_target_key))
                lines.append("txrx.execute_flood(core_subset, file_reader"
                             ", {}, {})".format(self._app_id, size))
                spinnman_reports.append_to_rerun_script(conf.config.get(
                    "SpecGeneration", "Binary_folder"), lines)

    def _check_if_theres_any_pre_placement_constraints_to_satisify(self):
        for vertex in self._partitionable_graph.vertices:
            virtual_chip_constraints = \
                pacman_utility_calls.locate_constraints_of_type(
                    vertex.constraints,
                    VertexRequiresVirtualChipInMachineConstraint)
            if len(virtual_chip_constraints) > 0:
                for virutal_chip_constrant in virtual_chip_constraints:
                    #check if the virtual chip doesnt already exist
                    if (self._machine.get_chip_at(
                            virutal_chip_constrant.virtual_chip_coords['x'],
                            virutal_chip_constrant.virtual_chip_coords['y'])
                            is None):
                        virutal_chip = \
                            self._create_virtual_chip(virutal_chip_constrant)
                        self._machine.add_chip(virutal_chip)

    def _create_virtual_chip(self, virtual_chip_constraint):
        sdram_object = SDRAM()
        #creates the two links
        to_virtual_chip_link = Link(
            destination_x=virtual_chip_constraint.virtual_chip_coords['x'],
            destination_y=virtual_chip_constraint.virtual_chip_coords['y'],
            source_x=virtual_chip_constraint.connected_to_chip_coords['x'],
            source_y=virtual_chip_constraint.connected_to_chip_coords['y'],
            multicast_default_from=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            multicast_default_to=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        from_virtual_chip_link = Link(
            destination_x=virtual_chip_constraint.connected_to_chip_coords['x'],
            destination_y=virtual_chip_constraint.connected_to_chip_coords['y'],
            source_x=virtual_chip_constraint.virtual_chip_coords['x'],
            source_y=virtual_chip_constraint.virtual_chip_coords['y'],
            multicast_default_from=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            multicast_default_to=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        #create the router
        links = [from_virtual_chip_link]
        router_object = MachineRouter(
            links=links, emergency_routing_enabled=False,
            clock_speed=MachineRouter.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint)

        #create the processors
        processors = list()
        for virtual_core_id in range(0, 128):
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))
        #connect the real chip with the virtual one
        connected_chip = self._machine.get_chip_at(
            virtual_chip_constraint.connected_to_chip_coords['x'],
            virtual_chip_constraint.connected_to_chip_coords['y'])
        connected_chip.router.add_link(to_virtual_chip_link)
        #return new v chip
        return Chip(
            processors=processors, router=router_object, sdram=sdram_object,
            x=virtual_chip_constraint.virtual_chip_coords['x'],
            y=virtual_chip_constraint.virtual_chip_coords['y'], virtual=True)