
# pacman imports
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge

# common front end imports
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.operations.pacman_algorithm_executor import PACMANAlgorithmExecutor
from spinn_front_end_common.interface.spinnaker_main_interface import \
    SpinnakerMainInterface
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities.utility_objs.executable_finder \
    import ExecutableFinder

# add pops pop view and assembly from the bloody same class.
from spynnaker.pyNN.models.population_based_objects import \
    Assembly, PopulationView, Population

from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN import overridden_pacman_functions
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.models.abstract_models\
    .abstract_send_me_multicast_commands_vertex \
    import AbstractSendMeMulticastCommandsVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_vertex_with_dependent_vertices \
    import AbstractVertexWithEdgeToDependentVertices
from spynnaker.pyNN.utilities import constants

# general imports
import logging
import math
import os

# global objects
logger = logging.getLogger(__name__)
executable_finder = ExecutableFinder()


class Spinnaker(SpinnakerMainInterface):
    """
    Spinnaker: the main entrance for the spynnaker front end
    """

    def __init__(
            self, host_name=None, timestep=None, min_delay=None,
            max_delay=None, graph_label=None, database_socket_addresses=None,
            n_chips_required=None):

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))

        # population holders
        self._populations = list()
        self._projections = list()

        # none labelled objects special to spynnaker
        self._none_labelled_pop_view_count = 0
        self._none_labelled_assembly_count = 0

        # atom holders for pop views and assemblers
        self._pop_atom_mappings = dict()
        self._pop_view_atom_mapping = dict()
        self._assemble_atom_mapping = dict()

        # command sender vertex
        self._multi_cast_vertex = None

        # set of LPG's used by the external device plugin module
        self._live_spike_recorder = dict()

        # create xml path for where to locate spynnaker related functions when
        # using auto pause and resume
        extra_algorithm_xml_path = list()
        extra_algorithm_xml_path.append(os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml"))

        extra_mapping_inputs = dict()
        extra_mapping_inputs['CreateAtomToEventIdMapping'] = config.getboolean(
            "Database", "create_routing_info_to_neuron_id_mapping")

        SpinnakerMainInterface.__init__(
            self, config, graph_label=graph_label,
            executable_finder=executable_finder,
            database_socket_addresses=database_socket_addresses,
            extra_algorithm_xml_paths=extra_algorithm_xml_path,
            extra_mapping_inputs=extra_mapping_inputs,
            n_chips_required=n_chips_required)

        # timing parameters
        self._min_supported_delay = None
        self._max_supported_delay = None
        self._time_scale_factor = None

        # set up machine targeted data
        self._set_up_timings(timestep, min_delay, max_delay)
        self.set_up_machine_specifics(host_name)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

    def _set_up_timings(self, timestep, min_delay, max_delay):
        self._machine_time_step = config.getint("Machine", "machineTimeStep")

        # deal with params allowed via the setup options
        if timestep is not None:

            # convert into milliseconds from microseconds
            timestep *= 1000
            self._machine_time_step = timestep

        if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
            raise common_exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step"
                .format(constants.MIN_SUPPORTED_DELAY * timestep))

        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS
        delay_extension_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS \
            * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extension_max_supported_delay

        if max_delay is not None\
           and float(max_delay * 1000) > max_delay_tics_supported * timestep:
            raise common_exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
            self._min_supported_delay = min_delay
        else:
            self._min_supported_delay = timestep / 1000.0

        if max_delay is not None:
            self._max_supported_delay = max_delay
        else:
            self._max_supported_delay = (max_delay_tics_supported *
                                         (timestep / 1000.0))

        if (config.has_option("Machine", "timeScaleFactor") and
                config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = \
                config.getint("Machine", "timeScaleFactor")
            if timestep * self._time_scale_factor < 1000:
                if config.getboolean(
                        "Mode", "violate_1ms_wall_clock_restriction"):
                    logger.warn(
                        "****************************************************")
                    logger.warn(
                        "*** The combination of simulation time step and  ***")
                    logger.warn(
                        "*** the machine time scale factor results in a   ***")
                    logger.warn(
                        "*** wall clock timer tick that is currently not  ***")
                    logger.warn(
                        "*** reliably supported by the spinnaker machine. ***")
                    logger.warn(
                        "****************************************************")
                else:
                    raise common_exceptions.ConfigurationException(
                        "The combination of simulation time step and the"
                        " machine time scale factor results in a wall clock "
                        "timer tick that is currently not reliably supported "
                        "by the spinnaker machine.  If you would like to "
                        "override this behaviour (at your own risk), please "
                        "add violate_1ms_wall_clock_restriction = True to the "
                        "[Mode] section of your .spynnaker.cfg file")
        else:
            self._time_scale_factor = max(1,
                                          math.ceil(1000.0 / float(timestep)))
            if self._time_scale_factor > 1:
                logger.warn("A timestep was entered that has forced sPyNNaker "
                            "to automatically slow the simulation down from "
                            "real time by a factor of {}. To remove this "
                            "automatic behaviour, please enter a "
                            "timescaleFactor value in your .spynnaker.cfg"
                            .format(self._time_scale_factor))

    def _detect_if_graph_has_changed(self, reset_flags=True):
        """ Iterates though the graph and looks changes
        """
        changed = False
        for population in self._populations:
            if population.requires_mapping:
                changed = True
            if reset_flags:
                population.mark_no_changes()

        for projection in self._projections:
            if projection.requires_mapping:
                changed = True
            if reset_flags:
                projection.mark_no_changes()

        return changed

    @property
    def min_supported_delay(self):
        """ The minimum supported delay based in milliseconds
        """
        return self._min_supported_delay

    @property
    def max_supported_delay(self):
        """ The maximum supported delay based in milliseconds
        """
        return self._max_supported_delay

    def add_partitionable_vertex(self, vertex_to_add):
        """

        :param vertex_to_add:
        :return:
        """
        if isinstance(vertex_to_add, CommandSender):
            self._multi_cast_vertex = vertex_to_add

        self._partitionable_graph.add_vertex(vertex_to_add)

        if isinstance(vertex_to_add, AbstractSendMeMulticastCommandsVertex):
            if self._multi_cast_vertex is None:
                self._multi_cast_vertex = CommandSender(
                    self._machine_time_step, self._time_scale_factor)
                self.add_partitionable_vertex(self._multi_cast_vertex)
            edge = MultiCastPartitionableEdge(
                self._multi_cast_vertex, vertex_to_add)
            self._multi_cast_vertex.add_commands(vertex_to_add.commands, edge)
            self.add_partitionable_edge(edge)

        # add any dependent edges and vertices if needed
        if isinstance(vertex_to_add,
                      AbstractVertexWithEdgeToDependentVertices):
            for dependant_vertex in vertex_to_add.dependent_vertices:
                self.add_partitionable_vertex(dependant_vertex)
                dependant_edge = MultiCastPartitionableEdge(
                    pre_vertex=vertex_to_add, post_vertex=dependant_vertex)
                self.add_partitionable_edge(
                    dependant_edge,
                    vertex_to_add.edge_partition_identifier_for_dependent_edge)

    def get_pop_atom_mapping(self):
        """
        supports getting the atom mappings needed for pop views and assemblers
        :return:
        """
        return self._pop_atom_mappings

    def get_pop_view_atom_mapping(self):
        return self._pop_view_atom_mapping

    def get_assembly_atom_mapping(self):
        return self._assemble_atom_mapping

    def create_population(self, size, cellclass, cellparams, structure, label):
        """

        :param size:
        :param cellclass:
        :param cellparams:
        :param structure:
        :param label:
        :return:
        """
        # build a population object
        population = Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self)
        self._add_population(population)
        return population

    def create_population_vew(
            self, population_to_view, neuron_selector, label):
        """

        :param population_to_view: population to filter over
        :param neuron_selector:

        neuron_selector -
        a slice or numpy mask array. The mask array should either be
           a boolean array of the same size as the parent, or an
           integer array containing cell indices, i.e. if p.size == 5,
             !PopulationView(p, array([False, False, True, False, True]))
             !PopulationView(p, array([2,4]))
             !PopulationView(p, slice(2,5,2))
           will all create the same view.
        :param label: the label of this pop view
        :return: a population view object
        """

        # build pop view
        population_view = PopulationView(
            population_to_view, neuron_selector, label, self)

        return population_view

    def create_assembly(self, populations, label):
        """

        :param populations: populations or pop views to be added to a assembly
        :param label: the label for this assembly
        :return: a assembly
        """
        # create assembler
        assembler = Assembly(populations, label, self)
        return assembler

    def _add_population(self, population):
        """ Called by each population to add itself to the list
        """
        self._populations.append(population)

    def _add_projection(self, projection):
        """ Called by each projection to add itself to the list
        """
        self._projections.append(projection)

    @property
    def none_labelled_pop_view_count(self):
        """ The number of times pop views have not been labelled.
        """
        return self._none_labelled_pop_view_count

    def increment_none_labelled_pop_view_count(self):
        """ Increment the number of new pop views which have not been labelled.
        """
        self._none_labelled_pop_view_count += 1

    @property
    def none_labelled_assembly_count(self):
        """ The number of times assembly have not been labelled.
        """
        return self._none_labelled_assembly_count

    def increment_none_labelled_assembly_count(self):
        """ Increment the number of new assemblies which have not been labelled.
        """
        self._none_labelled_assembly_count += 1

    def create_projection(
            self, presynaptic_population, postsynaptic_population, connector,
            source, target, synapse_dynamics, label, rng):
        """

        :param presynaptic_population: source pop this projection goes from
        :param postsynaptic_population: dest pop this projection goes to
        :param connector: the definition of which neurons connect to each other
        :param source:
        :param target: type of projection
        :param synapse_dynamics: plasticity object
        :param label: human readable version of the projection
        :param rng: the random number generator to use on this projection
        :return:
        """
        return Projection(
            presynaptic_population=presynaptic_population, label=label,
            postsynaptic_population=postsynaptic_population, rng=rng,
            connector=connector, source=source, target=target,
            synapse_dynamics=synapse_dynamics, spinnaker_control=self,
            machine_time_step=self._machine_time_step,
            timescale_factor=self._time_scale_factor)

    def stop(self, turn_off_machine=None, clear_routing_tables=None,
             clear_tags=None, extract_provenance_data=True,
             extract_iobuf=True):
        """
        :param turn_off_machine: decides if the machine should be powered down\
            after running the execution. Note that this powers down all boards\
            connected to the BMP connections given to the transceiver
        :type turn_off_machine: bool
        :param clear_routing_tables: informs the tool chain if it\
            should turn off the clearing of the routing tables
        :type clear_routing_tables: bool
        :param clear_tags: informs the tool chain if it should clear the tags\
            off the machine at stop
        :type clear_tags: boolean
        :param extract_provenance_data: informs the tools if it should \
            try to extract provenance data.
        :type extract_provenance_data: bool
        :param extract_iobuf: tells the tools if it should try to \
            extract iobuf
        :type extract_iobuf: bool
        :return: None
        """
        for population in self._populations:
            population._end()

        SpinnakerMainInterface.stop(
            self, turn_off_machine, clear_routing_tables, clear_tags,
            extract_provenance_data, extract_iobuf)

    def run(self, run_time):
        """ Run the model created

        :param run_time: the time in ms to run the simulation for
        """

        # extra post run algorithms
        self._dsg_algorithm = "SpynnakerDataSpecificationWriter"

        # run grouper again if changes requires mapping
        if self._detect_if_graph_has_changed(reset_flags=False):
            self._execute_grouper_algorithm()
            self._partitioned_graph = PartitionedGraph(
                label=self._partitioned_graph.label)
            self._graph_mapper = None

        # run basic spinnaker
        SpinnakerMainInterface.run(self, run_time)

    def _execute_grouper_algorithm(self):
        """
        execute the grouper algorithm.
        :return: None
        """

        # build executor
        inputs = dict()
        inputs['PopulationAtomMapping'] = self._pop_atom_mappings
        inputs['PopulationViewAtomMapping'] = self._pop_view_atom_mapping
        inputs['AssemblyAtomMapping'] = self._assemble_atom_mapping
        inputs['Projections'] = self._projections
        inputs['MachineTimeStep'] = self._machine_time_step
        inputs['TimeScaleFactor'] = self._time_scale_factor
        inputs['UserMaxDelay'] = self.max_supported_delay
        inputs['VirtualBoardFlag'] = self._use_virtual_board

        outputs = ["MemoryPartitionableGraph", "PopToVertexMapping"]
        algorithms = list()
        algorithms.append("Grouper")
        xml_paths = list()
        xml_paths.append(os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml"))
        pacman_executor = PACMANAlgorithmExecutor(
            algorithms=algorithms, inputs=inputs, required_outputs=outputs,
            optional_algorithms=[], xml_paths=xml_paths)
        pacman_executor.execute_mapping()

        # get partitionable graph
        self._partitionable_graph = \
            pacman_executor.get_item("MemoryPartitionableGraph")
        pop_to_vertex_mapping = pacman_executor.get_item("PopToVertexMapping")
        vertex_to_pop_mapping = pacman_executor.get_item("VertexToPopMapping")

        # update each population with their own mapping
        for pop in self._populations:
            pop.set_mapping(pop_to_vertex_mapping[pop])

        for vertex in vertex_to_pop_mapping:
            vertex.set_mapping(vertex_to_pop_mapping[vertex])
