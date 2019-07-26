# Copyright (c) 2017-2019 The University of Manchester
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

from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from six import iteritems
try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
import math
import struct
import sys
import numpy
import scipy.stats  # @UnresolvedImport
from scipy import special  # @UnresolvedImport

from spinn_utilities.overrides import overrides

from spinn_utilities.helpful_functions import get_valid_components

from pacman.model.graphs.application import ApplicationVertex
from pacman.executor.injection_decorator import inject_items
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from pacman.model.constraints.placer_constraints\
    import SameChipAsConstraint

from data_specification.enums import DataType

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spinn_front_end_common.utilities import (
    constants as common_constants, helpful_functions, globals_variables)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.profiling import profile_utils
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
    AbstractProvidesIncomingPartitionConstraints, AbstractChangableAfterRun)
from spinn_front_end_common.interface.simulation import simulation_utilities

from spynnaker.pyNN.models.neuron.generator_data import GeneratorData
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector, AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neuron import master_pop_table_generators
from spynnaker.pyNN.models.neuron import PopulationMachineVertex
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, AbstractSynapseDynamicsStructural,
    AbstractGenerateOnMachine)
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex
from spynnaker.pyNN.utilities.constants import (
    POPULATION_BASED_REGIONS, POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.utility_calls import (
    get_maximum_probable_value, get_n_bits)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.models.common import (
    AbstractSynapseRecordable, SynapseRecorder)
from .synapse_machine_vertex import SynapseMachineVertex
from .key_space_tracker import KeySpaceTracker

TIME_STAMP_BYTES = 4

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 36
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 12
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8

# 4 for n_edges
# 8 for post_vertex_slice.lo_atom, post_vertex_slice.n_atoms
# 4 for n_synapse_types
# 4 for n_synapse_type_bits
# 4 for n_synapse_index_bits
_SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = 4 + 8 + 4 + 4 + 4

# Amount to scale synapse SDRAM estimate by to make sure the synapses fit
_SYNAPSE_SDRAM_OVERSCALE = 1.1

_ONE_WORD = struct.Struct("<I")


class SynapticManager(
        ApplicationVertex, AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
        AbstractProvidesIncomingPartitionConstraints, AbstractAcceptsIncomingSynapses,
        AbstractSynapseRecordable, AbstractChangableAfterRun):
    """ Deals with synapses
    """
    # pylint: disable=too-many-arguments, too-many-locals
    __slots__ = [
        "__delay_key_index",
        "_implemented_synapse_types", #number of different synapse types implemented (set to one on higher level, but left as param here)
        "_synapse_index", #index of the synapse type implemented, MUST be 0 if implemented_synapse_types is > 1
        "__one_to_one_connection_dtcm_max_bytes",
        "__poptable_type",
        "__pre_run_connection_holders",
        "__retrieved_blocks",
        "_weight_scale",
        "__ring_buffer_sigma",
        "__spikes_per_second",
        "__synapse_dynamics",
        "__synapse_io",
        "__weight_scales",
        "__ring_buffer_shifts",
        "__gen_on_machine",
        "__max_row_info",
        "__synapse_indices",
        "__max_row_info",
        "_n_atoms",
        "_n_profile_samples",
        "_vertex",
        "_n_profile_samples",
        "_incoming_spike_buffer_size",
        "_machine_vertices",
        "_connected_app_vertices",
        "_model_synapse_types",
        "_atoms_neuron_cores",
        "__synapse_recorder",
        "__partition",
        "_atoms_offset",
        "_ring_buffer_shifts",
        "_slice_list",
        "__change_requires_mapping"]

    BASIC_MALLOC_USAGE = 2

    BYTES_FOR_SYNAPSE_PARAMS = 36

    _n_vertices = 0

    RECORDABLES = ["synapse"]

    def __init__(self, n_synapse_types, synapse_index, n_neurons, atoms_offset,
                 constraints, label, max_atoms_per_core, weight_scale, ring_buffer_sigma,
                 spikes_per_second, incoming_spike_buffer_size, model_syn_types,
                 population_table_type=None, synapse_io=None):

        self._implemented_synapse_types = n_synapse_types
        self.__ring_buffer_sigma = ring_buffer_sigma
        self.__spikes_per_second = spikes_per_second
        self._n_atoms = n_neurons
        self._weight_scale = weight_scale
        self._machine_vertices = dict()
        self._connected_app_vertices = None
        self._model_synapse_types = model_syn_types
        self._atoms_neuron_cores = max_atoms_per_core
        self._atoms_offset = atoms_offset
        # Hardcoded, avoids the function call and is set to the same value for all the partitions
        self._ring_buffer_shifts = [2]
        self._slice_list = None

        #FOR RECORDING
        recordables = ["synapse"]
        self.__synapse_recorder = SynapseRecorder(recordables, n_neurons)
        self.__change_requires_mapping = True

        if self._implemented_synapse_types > 1:
            # Hard coded to ensure it's 0.
            # Used at C level to compute SDRAM offsets
            self._synapse_index = 0
        else:
            self._synapse_index = synapse_index

        config = globals_variables.get_simulator().config

        self._incoming_spike_buffer_size = incoming_spike_buffer_size

        if incoming_spike_buffer_size is None:
            self._incoming_spike_buffer_size = config.getint(
                "Simulation", "incoming_spike_buffer_size")

        self._vertex = super(SynapticManager, self).__init__(
            label, constraints, max_atoms_per_core)

        #MIGHT NEED WORK FOR DUAL EXC SYN TYPES
        self.__partition = 0 if ("low" in label.split("_") or self._synapse_index > 1) else 2


        # Get the type of population table
        self.__poptable_type = population_table_type
        if population_table_type is None:
            population_table_type = ("MasterPopTableAs" + config.get(
                "MasterPopTable", "generator"))
            algorithms = get_valid_components(
                master_pop_table_generators, "master_pop_table_as")
            self.__poptable_type = algorithms[population_table_type]()

        # Get the synapse IO
        self.__synapse_io = synapse_io
        if synapse_io is None:
            self.__synapse_io = SynapseIORowBased()

        if self.__ring_buffer_sigma is None:
            self.__ring_buffer_sigma = config.getfloat(
                "Simulation", "ring_buffer_sigma")

        if self.__spikes_per_second is None:
            self.__spikes_per_second = config.getfloat(
                "Simulation", "spikes_per_second")

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self.__synapse_dynamics = SynapseDynamicsStatic()

        # Keep the details once computed to allow reading back
        self.__weight_scales = dict()
        self.__ring_buffer_shifts = None
        self.__delay_key_index = dict()
        self.__retrieved_blocks = dict()

        # A list of connection holders to be filled in pre-run, indexed by
        # the edge the connection is for
        self.__pre_run_connection_holders = defaultdict(list)

        # Limit the DTCM used by one-to-one connections
        self.__one_to_one_connection_dtcm_max_bytes = config.getint(
            "Simulation", "one_to_one_connection_dtcm_max_bytes")

        # Whether to generate on machine or not for a given vertex slice
        self.__gen_on_machine = dict()

        # A map of synapse information to maximum row / delayed row length and
        # size in bytes
        self.__max_row_info = dict()

        # A map of synapse information for each machine pre vertex to index
        self.__synapse_indices = dict()

        # Set up for profiling
        self._n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

    @property
    def get_vertex(self):
        return self._vertex

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    def atoms_offset(self):
        return self._atoms_offset

    @property
    def synapse_dynamics(self):
        return self.__synapse_dynamics

    def set_synapse_dynamics(self, synapse_dynamics):

        # We can always override static dynamics or None
        if isinstance(self.__synapse_dynamics, SynapseDynamicsStatic):
            self.__synapse_dynamics = synapse_dynamics

        # We can ignore a static dynamics trying to overwrite a plastic one
        elif isinstance(synapse_dynamics, SynapseDynamicsStatic):
            pass

        # Otherwise, the dynamics must be equal
        elif not synapse_dynamics.is_same_as(self.__synapse_dynamics):
            raise SynapticConfigurationException(
                "Synapse dynamics must match exactly when using multiple edges"
                "to the same population")

    @property
    def ring_buffer_sigma(self):
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    @property
    def weight_scale(self):
        return self._weight_scale

    @property
    def implemented_synapse_types(self):
        return self._implemented_synapse_types

    @property
    def synapse_index(self):
        return self._synapse_index

    @property
    def _synapse_recorder(self):
        return self.__synapse_recorder

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

    @overrides(AbstractAcceptsIncomingSynapses.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        return self._synapse_index

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self.__synapse_io.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @property
    def vertex_executable_suffix(self):
        return self.__synapse_dynamics.get_vertex_executable_suffix()

    @property
    def ring_buffer_shifts(self):
        return self._ring_buffer_shifts

    @property
    def connected_app_vertices(self):
        return self._connected_app_vertices

    @connected_app_vertices.setter
    def connected_app_vertices(self, connected_app_vertices):
        self._connected_app_vertices = connected_app_vertices

    @property
    def slice_list(self):
        return self._slice_list

    @slice_list.setter
    def slice_list(self, slices):
        self._slice_list = slices

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        #return self.vertex_executable_suffix + "_syn.aplx"
        return "Static_synapse.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self.__pre_run_connection_holders[edge, synapse_info].append(
            connection_holder)

    def get_n_cpu_cycles(self, vertex_slice):
        return (
            _SYNAPSES_BASE_N_CPU_CYCLES +
            _SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON * vertex_slice.n_atoms +
            self.__synapse_recorder.get_n_cpu_cycles(vertex_slice.n_atoms))

    def _get_number_of_mallocs_used_by_dsg(self):
        #TODO: add recording part
        return self.BASIC_MALLOC_USAGE

    @inject_items({
        "graph": "MemoryApplicationGraph",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={
            "graph", "machine_time_step"
        }
    )
    def get_resources_used_by_atoms(
            self, vertex_slice, graph, machine_time_step):
        # pylint: disable=arguments-differ

        #Region for recording
        variableSDRAM = self.__synapse_recorder.get_variable_sdram_usage(
            vertex_slice)

        constantSDRAM = ConstantSDRAM(self.get_sdram_usage_in_bytes(
            vertex_slice, graph, machine_time_step))

        # set resources required from this object
        container = ResourceContainer(
            sdram=variableSDRAM + constantSDRAM,
            dtcm=DTCMResource(self.get_dtcm_usage_in_bytes(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_n_cpu_cycles(vertex_slice)))

        # return the total resources.
        return container

    def get_dtcm_usage_in_bytes(self, vertex_slice):
        return (
            _SYNAPSES_BASE_DTCM_USAGE_IN_BYTES +
            self.__synapse_recorder.get_dtcm_usage_in_bytes(vertex_slice))

    def _get_synapse_params_size(self, vertex_slice):
        # Params plus ring buffer left shift
        return (self.BYTES_FOR_SYNAPSE_PARAMS +
                self._implemented_synapse_types * 4 +
                self.__synapse_recorder.get_sdram_usage_in_bytes(vertex_slice))

    def _get_static_synaptic_matrix_sdram_requirements(self):

        # 4 for address of direct addresses, and
        # 4 for the size of the direct addresses matrix in bytes
        return 8

    def _get_max_row_info(
            self, synapse_info, post_vertex_slice, app_edge,
            machine_time_step):
        """ Get the maximum size of each row for a given slice of the vertex
        """
        key = (synapse_info, post_vertex_slice.lo_atom,
               post_vertex_slice.hi_atom)
        if key not in self.__max_row_info:
            self.__max_row_info[key] = self.__synapse_io.get_max_row_info(
                synapse_info, post_vertex_slice,
                app_edge.n_delay_stages, self.__poptable_type,
                machine_time_step, app_edge)
        return self.__max_row_info[key]

    def _get_synaptic_blocks_size(
            self, post_vertex_slice, in_edges, machine_time_step):
        """ Get the size of the synaptic blocks in bytes
        """
        memory_size = self._get_static_synaptic_matrix_sdram_requirements()
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):
                for synapse_info in in_edge.synapse_information:
                    memory_size = self.__add_synapse_size(
                        memory_size, synapse_info, post_vertex_slice, in_edge,
                        machine_time_step)
        return int(memory_size * _SYNAPSE_SDRAM_OVERSCALE)

    def __add_synapse_size(self, memory_size, synapse_info, post_vertex_slice,
                           in_edge, machine_time_step):
        max_row_info = self._get_max_row_info(
            synapse_info, post_vertex_slice, in_edge, machine_time_step)
        n_atoms = in_edge.pre_vertex.n_atoms
        memory_size = self.__poptable_type.get_next_allowed_address(
            memory_size)
        memory_size += max_row_info.undelayed_max_bytes * n_atoms
        memory_size = self.__poptable_type.get_next_allowed_address(
            memory_size)
        memory_size += (
            max_row_info.delayed_max_bytes * n_atoms * in_edge.n_delay_stages)
        return memory_size

    def _get_size_of_generator_information(self, in_edges):
        """ Get the size of the synaptic expander parameters
        """
        gen_on_machine = False
        size = 0
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):
                for synapse_info in in_edge.synapse_information:

                    # Get the number of likely vertices
                    max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                    if in_edge.pre_vertex.n_atoms < max_atoms:
                        max_atoms = in_edge.pre_vertex.n_atoms
                    n_edge_vertices = int(math.ceil(
                        float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))

                    # Get the size
                    connector = synapse_info.connector
                    dynamics = synapse_info.synapse_dynamics
#                    weights = synapse_info.weight
#                    delays = synapse_info.delay
                    connector_gen = isinstance(
                        connector, AbstractGenerateConnectorOnMachine) and \
                        connector.generate_on_machine(
                            synapse_info.weight, synapse_info.delay)
                    synapse_gen = isinstance(
                        dynamics, AbstractGenerateOnMachine)
                    if connector_gen and synapse_gen:
                        gen_on_machine = True
                        gen_size = sum((
                            GeneratorData.BASE_SIZE,
                            connector.gen_delay_params_size_in_bytes(
                                synapse_info.delay),
                            connector.gen_weight_params_size_in_bytes(
                                synapse_info.weight),
                            connector.gen_connector_params_size_in_bytes,
                            dynamics.gen_matrix_params_size_in_bytes
                        ))
                        size += gen_size * n_edge_vertices
        if gen_on_machine:
            size += _SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES
            size += self._implemented_synapse_types * 4
        return size

    def _get_synapse_dynamics_parameter_size(self, vertex_slice,
                                             in_edges=None):
        """ Get the size of the synapse dynamics region
        """
        # Does the size of the parameters area depend on presynaptic
        # connections in any way?
        if isinstance(self.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._implemented_synapse_types,
                in_edges=in_edges)
        else:
            return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._implemented_synapse_types)

    def get_sdram_usage_in_bytes(
            self, vertex_slice, graph, machine_time_step):
        n_record = len(self.RECORDABLES)
        in_edges = graph.get_edges_ending_at_vertex(self)
        return (
            common_constants.SYSTEM_BYTES_REQUIREMENT +
            self._get_synapse_params_size(vertex_slice) +
            self._get_synapse_dynamics_parameter_size(vertex_slice, in_edges=in_edges) +
            self._get_synaptic_blocks_size(
                vertex_slice, in_edges, machine_time_step) +
            self.__poptable_type.get_master_population_table_size(
                vertex_slice, in_edges) +
            self._get_size_of_generator_information(in_edges) +
            (self._get_number_of_mallocs_used_by_dsg() *
             common_constants.SARK_PER_MALLOC_SDRAM_USAGE) +
            recording_utilities.get_recording_header_size(n_record) +
            recording_utilities.get_recording_data_constant_size(n_record) +
            SynapseMachineVertex.get_provenance_data_size(
                SynapseMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            profile_utils.get_profile_region_size(
                self._n_profile_samples)
        )

    def _reserve_synapse_param_data_region(self, spec, vertex_slice):
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(vertex_slice),
            label='SynapseParams')

    def _reserve_memory_regions(
            self, spec, machine_vertex, vertex_slice,
            machine_graph, all_syn_block_sz, graph_mapper):

        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYSTEM.value,
            size=common_constants.SYSTEM_BYTES_REQUIREMENT,
            label="SystemRegion"
        )

        self._reserve_synapse_param_data_region(spec, vertex_slice)

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.RECORDING.value,
            size=recording_utilities.get_recording_header_size(
                len(self.RECORDABLES)))

        master_pop_table_sz = \
            self.__poptable_type.get_exact_master_population_table_size(
                machine_vertex, machine_graph, graph_mapper)
        if master_pop_table_sz > 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
                size=master_pop_table_sz, label='PopTable')
        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                size=all_syn_block_sz, label='SynBlocks')

        synapse_dynamics_sz = \
            self._get_synapse_dynamics_parameter_size(
                vertex_slice,
                machine_graph.get_edges_ending_at_vertex(machine_vertex))
        if synapse_dynamics_sz != 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                size=synapse_dynamics_sz, label='synapseDynamicsParams')

        profile_utils.reserve_profile_region(
            spec, POPULATION_BASED_REGIONS.PROFILING.value,
            self._n_profile_samples)

        machine_vertex.reserve_provenance_data_region(spec)

    def get_number_of_mallocs_used_by_dsg(self):
        return 4

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second,
            machine_timestep, n_synapses_in, sigma):
        """ Provides expected upper bound on accumulated values in a ring\
            buffer element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in\
        and timestep.

        All arguments should be assumed real values except n_synapses_in\
        which will be an integer.

        :param weight_mean: Mean of weight distribution (in either nA or\
            microSiemens as required)
        :param weight_std_dev: SD of weight distribution
        :param spikes_per_second: Maximum expected Poisson rate in Hz
        :param machine_timestep: in us
        :param n_synapses_in: No of connected synapses
        :param sigma: How many SD above the mean to go for upper bound; a\
            good starting choice is 5.0. Given length of simulation we can\
            set this for approximate number of saturation events.
        """
        # E[ number of spikes ] in a timestep
        steps_per_second = 1000000.0 / machine_timestep
        average_spikes_per_timestep = (
            float(n_synapses_in * spikes_per_second) / steps_per_second)

        # Exact variance contribution from inherent Poisson variation
        poisson_variance = average_spikes_per_timestep * (weight_mean ** 2)

        # Upper end of range for Poisson summation required below
        # upper_bound needs to be an integer
        upper_bound = int(round(average_spikes_per_timestep +
                                POSSION_SIGMA_SUMMATION_LIMIT *
                                math.sqrt(average_spikes_per_timestep)))

        # Closed-form exact solution for summation that gives the variance
        # contributed by weight distribution variation when modulated by
        # Poisson PDF.  Requires scipy.special for gamma and incomplete gamma
        # functions. Beware: incomplete gamma doesn't work the same as
        # Mathematica because (1) it's regularised and needs a further
        # multiplication and (2) it's actually the complement that is needed
        # i.e. 'gammaincc']

        weight_variance = 0.0

        if weight_std_dev > 0:
            lngamma = special.gammaln(1 + upper_bound)
            gammai = special.gammaincc(
                1 + upper_bound, average_spikes_per_timestep)

            big_ratio = (math.log(average_spikes_per_timestep) * upper_bound -
                         lngamma)

            if -701.0 < big_ratio < 701.0 and big_ratio != 0.0:
                log_weight_variance = (
                    -average_spikes_per_timestep +
                    math.log(average_spikes_per_timestep) +
                    2.0 * math.log(weight_std_dev) +
                    math.log(math.exp(average_spikes_per_timestep) * gammai -
                             math.exp(big_ratio)))
                weight_variance = math.exp(log_weight_variance)

        # upper bound calculation -> mean + n * SD
        return ((average_spikes_per_timestep * weight_mean) +
                (sigma * math.sqrt(poisson_variance + weight_variance)))

    def _get_ring_buffer_to_input_left_shifts(
            self, application_vertex, application_graph, machine_timestep):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """
        weight_scale_squared = self._weight_scale * self._weight_scale
        n_synapse_types = self._model_synapse_types
        running_totals = [RunningStats() for _ in range(n_synapse_types)]
        delay_running_totals = [RunningStats() for _ in range(n_synapse_types)]
        total_weights = numpy.zeros(n_synapse_types)
        biggest_weight = numpy.zeros(n_synapse_types)
        weights_signed = False
        rate_stats = [RunningStats() for _ in range(n_synapse_types)]
        steps_per_second = 1000000.0 / machine_timestep

        for app_edge in application_graph.get_edges_ending_at_vertex(
                application_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    synapse_type = synapse_info.synapse_type
                    synapse_dynamics = synapse_info.synapse_dynamics
                    connector = synapse_info.connector

                    weight_mean = (
                        synapse_dynamics.get_weight_mean(
                            connector, synapse_info.weight) * self._weight_scale)
                    n_connections = \
                        connector.get_n_connections_to_post_vertex_maximum()
                    weight_variance = synapse_dynamics.get_weight_variance(
                        connector, synapse_info.weight) * weight_scale_squared
                    running_totals[synapse_type].add_items(
                        weight_mean, weight_variance, n_connections)

                    delay_variance = synapse_dynamics.get_delay_variance(
                        connector, synapse_info.delay)
                    delay_running_totals[synapse_type].add_items(
                        0.0, delay_variance, n_connections)

                    weight_max = (synapse_dynamics.get_weight_maximum(
                        connector, synapse_info.weight) * self._weight_scale)
                    biggest_weight[synapse_type] = max(
                        biggest_weight[synapse_type], weight_max)

                    spikes_per_tick = max(
                        1.0, self.__spikes_per_second / steps_per_second)
                    spikes_per_second = self.__spikes_per_second
                    if isinstance(app_edge.pre_vertex,
                                  SpikeSourcePoissonVertex):
                        rate = app_edge.pre_vertex.max_rate
                        # If non-zero rate then use it; otherwise keep default
                        if (rate != 0):
                            spikes_per_second = rate
                        if hasattr(spikes_per_second, "__getitem__"):
                            spikes_per_second = numpy.max(spikes_per_second)
                        elif get_simulator().is_a_pynn_random(
                                spikes_per_second):
                            spikes_per_second = get_maximum_probable_value(
                                spikes_per_second, app_edge.pre_vertex.n_atoms)
                        prob = 1.0 - (
                            (1.0 / 100.0) / app_edge.pre_vertex.n_atoms)
                        spikes_per_tick = spikes_per_second / steps_per_second
                        spikes_per_tick = scipy.stats.poisson.ppf(
                            prob, spikes_per_tick)
                    rate_stats[synapse_type].add_items(
                        spikes_per_second, 0, n_connections)
                    total_weights[synapse_type] += spikes_per_tick * (
                        weight_max * n_connections)

                    if synapse_dynamics.are_weights_signed():
                        weights_signed = True

        max_weights = numpy.zeros(n_synapse_types)
        for synapse_type in range(n_synapse_types):
            stats = running_totals[synapse_type]
            rates = rate_stats[synapse_type]
            if delay_running_totals[synapse_type].variance == 0.0:
                max_weights[synapse_type] = max(total_weights[synapse_type],
                                                biggest_weight[synapse_type])
            else:
                max_weights[synapse_type] = min(
                    self._ring_buffer_expected_upper_bound(
                        stats.mean, stats.standard_deviation, rates.mean,
                        machine_timestep, stats.n_items,
                        self.__ring_buffer_sigma),
                    total_weights[synapse_type])
                max_weights[synapse_type] = max(
                    max_weights[synapse_type], biggest_weight[synapse_type])

        # Convert these to powers
        max_weight_powers = (
            0 if w <= 0 else int(math.ceil(max(0, math.log(w, 2))))
            for w in max_weights)

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = (
            w + 1 if (2 ** w) <= a else w
            for w, a in zip(max_weight_powers, max_weights))

        # If we have synapse dynamics that uses signed weights,
        # Add another bit of shift to prevent overflows
        if weights_signed:
            max_weight_powers = (m + 1 for m in max_weight_powers)

        return [list(max_weight_powers)[self._synapse_index]]

        #return list(max_weight_powers)

    @staticmethod
    def _get_weight_scale(ring_buffer_to_input_left_shift):
        """ Return the amount to scale the weights by to convert them from \
            floating point values to 16-bit fixed point numbers which can be \
            shifted left by ring_buffer_to_input_left_shift to produce an\
            s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def _write_pop_table_padding(self, spec, next_block_start_address):
        next_block_allowed_address = self.__poptable_type\
            .get_next_allowed_address(next_block_start_address)
        padding = next_block_allowed_address - next_block_start_address
        if padding != 0:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required padding\n")
            self._write_padding(spec, padding, 0xDD)
            return next_block_allowed_address
        return next_block_start_address

    def _write_padding(self, spec, length, value):
        spec.set_register_value(register_id=15, data=length)
        spec.write_repeated_value(
            data=value, repeats=15, repeats_is_register=True,
            data_type=DataType.UINT8)

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, post_slices, post_slice_index, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_table_region, synaptic_matrix_region,
            direct_matrix_region, routing_info,
            graph_mapper, machine_graph, machine_time_step):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        block_addr = 0

        # Get the application projection edges incoming to this machine vertex
        in_machine_edges = machine_graph.get_edges_ending_at_vertex(
            machine_vertex)
        in_edges_by_app_edge = defaultdict(list)
        key_space_tracker = KeySpaceTracker()
        for edge in in_machine_edges:
            rinfo = routing_info.get_routing_info_for_edge(edge)
            key_space_tracker.allocate_keys(rinfo)
            app_edge = graph_mapper.get_application_edge(edge)
            if isinstance(app_edge, ProjectionApplicationEdge):
                in_edges_by_app_edge[app_edge].append(edge)

        # Set up the master population table
        self.__poptable_type.initialise_table(spec, master_pop_table_region)

        # Set up for single synapses - write the offset of the single synapses
        # initially 0
        single_synapses = list()
        spec.switch_write_focus(synaptic_matrix_region)
        single_addr = 0

        # Store a list of synapse info to be generated on the machine
        generate_on_machine = list()

        # For each machine edge in the vertex, create a synaptic list
        for app_edge, m_edges in iteritems(in_edges_by_app_edge):

            spec.comment("\nWriting matrix for edge:{}\n".format(
                app_edge.label))
            app_key_info = self.__app_key_and_mask(
                graph_mapper, m_edges, routing_info, key_space_tracker)
            d_app_key_info = self.__delay_app_key_and_mask(
                graph_mapper, m_edges, app_edge, key_space_tracker)
            pre_slices = list()
            for v in app_edge.pre_vertex.slice_list:
                pre_slices.extend(graph_mapper.get_slices(v))

            for synapse_info in app_edge.synapse_information:

                connector = synapse_info.connector
                dynamics = synapse_info.synapse_dynamics

                # If we can generate the connector on the machine, do so
                if (isinstance(
                        connector, AbstractGenerateConnectorOnMachine) and
                        connector.generate_on_machine(
                            synapse_info.weight, synapse_info.delay) and
                        isinstance(dynamics, AbstractGenerateOnMachine) and
                        dynamics.generate_on_machine and
                        not self.__is_app_edge_direct(
                            app_edge, synapse_info, m_edges, graph_mapper,
                            post_vertex_slice, single_addr)):
                    generate_on_machine.append(
                        (app_edge, m_edges, synapse_info, app_key_info,
                         d_app_key_info, pre_slices))
                else:
                    scales = list()
                    if self._synapse_index == 0:
                        scales.extend(weight_scales)
                        scales.append(0)
                    else:
                        scales.append(0)
                        scales.extend(weight_scales)
                    block_addr, single_addr = self.__write_matrix(
                        m_edges, graph_mapper, synapse_info, pre_slices,
                        post_slices, post_slice_index, post_vertex_slice,
                        app_edge, weight_scales, machine_time_step,
                        app_key_info, d_app_key_info, block_addr, single_addr,
                        spec, master_pop_table_region, all_syn_block_sz,
                        single_synapses, routing_info)

        # Skip blocks that will be written on the machine, but add them
        # to the master population table
        generator_data = list()
        for gen_data in generate_on_machine:
            (app_edge, m_edges, synapse_info, app_key_info, d_app_key_info,
             pre_slices) = gen_data
            block_addr = self.__write_on_chip_matrix_data(
                m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
                post_slice_index, post_vertex_slice, app_edge,
                machine_time_step, app_key_info, d_app_key_info, block_addr,
                spec, master_pop_table_region, all_syn_block_sz,
                generator_data, routing_info)

        self.__poptable_type.finish_master_pop_table(
            spec, master_pop_table_region)

        # Write the size and data of single synapses to the direct region
        if single_synapses:
            single_data = numpy.concatenate(single_synapses)
            spec.reserve_memory_region(
                region=direct_matrix_region,
                size=(len(single_data) * 4) + 4,
                label='DirectMatrix')
            spec.switch_write_focus(direct_matrix_region)
            spec.write_value(len(single_data) * 4)
            spec.write_array(single_data)
        else:
            spec.reserve_memory_region(
                region=direct_matrix_region, size=4, label="DirectMatrix")
            spec.switch_write_focus(direct_matrix_region)
            spec.write_value(0)

        return generator_data

    def __is_app_edge_direct(
            self, app_edge, synapse_info, m_edges, graph_mapper,
            post_vertex_slice, single_addr):
        next_single_addr = single_addr
        for m_edge in m_edges:
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            if not self.__is_direct(
                    next_single_addr, synapse_info, pre_slice,
                    post_vertex_slice, app_edge.n_delay_stages > 0):
                return False
            next_single_addr += pre_slice.n_atoms * 4
        return True

    def __write_matrix(
            self, m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
            post_slice_index, post_vertex_slice, app_edge, weight_scales,
            machine_time_step, app_key_info, delay_app_key_info, block_addr,
            single_addr, spec, master_pop_table_region, all_syn_block_sz,
            single_synapses, routing_info):
        # Write the synaptic matrix for an incoming application vertex
        max_row_info = self._get_max_row_info(
            synapse_info, post_vertex_slice, app_edge, machine_time_step)
        is_undelayed = bool(max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(max_row_info.delayed_max_n_synapses)
        undelayed_matrix_data = list()
        delayed_matrix_data = list()
        tmp_index = None
        tmp_d_index = None
        for m_edge in m_edges:
            # Get a synaptic matrix for each machine edge
            pre_idx = graph_mapper.get_machine_vertex_index(m_edge.pre_vertex)
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            (row_data, delayed_row_data) = self.__get_row_data(
                synapse_info, pre_slices, pre_idx, post_slices,
                post_slice_index, pre_slice, post_vertex_slice, app_edge,
                self._implemented_synapse_types, weight_scales, machine_time_step,
                m_edge, max_row_info)
            # If there is a single edge here, we allow the one-to-one direct
            # matrix to be used by using write_machine_matrix; it will make
            # no difference if this isn't actually a direct edge since there
            # is only one anyway...
            if app_key_info is None or len(m_edges) == 1:
                r_info = routing_info.get_routing_info_for_edge(m_edge)
                block_addr, single_addr, index = self.__write_machine_matrix(
                    block_addr, single_addr, spec, master_pop_table_region,
                    max_row_info.undelayed_max_n_synapses,
                    max_row_info.undelayed_max_words, r_info, row_data,
                    synapse_info, pre_slice, post_vertex_slice,
                    single_synapses, all_syn_block_sz, is_delayed)

                if tmp_index is None:
                    tmp_index = index
                elif tmp_index != index:
                    raise Exception("Indices different on different subvertices")

            elif is_undelayed:
                # If there is an app_key, save the data to be written later
                # Note: row_data will not be blank here since we told it to
                # generate a matrix of a given size
                undelayed_matrix_data.append(
                    (m_edge, pre_slice, row_data))

            if delay_app_key_info is None:
                delay_key = (app_edge.pre_vertex,
                             pre_slice.lo_atom, pre_slice.hi_atom)
                r_info = self.__delay_key_index.get(delay_key, None)
                block_addr, single_addr, d_index = self.__write_machine_matrix(
                    block_addr, single_addr, spec, master_pop_table_region,
                    max_row_info.delayed_max_n_synapses,
                    max_row_info.delayed_max_words, r_info, delayed_row_data,
                    synapse_info, pre_slice, post_vertex_slice,
                    single_synapses, all_syn_block_sz, True)

                if tmp_d_index is None:
                    tmp_d_index = d_index
                elif tmp_d_index != d_index:
                    raise Exception("Indices different on different subvertices")

            elif is_delayed:
                # If there is a delay_app_key, save the data for delays
                # Note delayed_row_data will not be blank as above.
                delayed_matrix_data.append(
                    (m_edge, pre_slice, delayed_row_data))

        # If there is an app key, add a single matrix and entry
        # to the population table but also put in padding
        # between tables when necessary
        if app_key_info is not None and len(m_edges) > 1:
            block_addr, index = self.__write_app_matrix(
                block_addr, spec, master_pop_table_region,
                max_row_info.undelayed_max_words,
                max_row_info.undelayed_max_bytes, app_key_info,
                undelayed_matrix_data, all_syn_block_sz, 1)

            if tmp_index is None:
                tmp_index = index
            elif tmp_index != index:
                raise Exception("Indices different on different subvertices")

        if delay_app_key_info is not None:
            block_addr, d_index = self.__write_app_matrix(
                block_addr, spec, master_pop_table_region,
                max_row_info.delayed_max_words, max_row_info.delayed_max_bytes,
                delay_app_key_info, delayed_matrix_data, all_syn_block_sz,
                app_edge.n_delay_stages)

            if tmp_d_index is None:
                tmp_d_index = d_index
            elif tmp_d_index != d_index:
                raise Exception("Indices different on different subvertices")

        if tmp_index is not None and tmp_d_index is not None and tmp_index != tmp_d_index:
            raise Exception("Delay index {} and normal index {} do not match"
                            .format(tmp_d_index, tmp_index))

        key = (synapse_info, post_vertex_slice.lo_atom)
        self.__synapse_indices[key] = tmp_index

        return block_addr, single_addr

    def __write_app_matrix(
            self, block_addr, spec, master_pop_table_region, max_words,
            max_bytes, app_key_info, matrix_data, all_syn_block_sz, n_ranges):
        # If there are no synapses, just write an invalid pop table entry
        if max_words == 0:
            index = self.__poptable_type.add_invalid_entry(
                spec, app_key_info.key_and_mask, app_key_info.core_mask,
                app_key_info.core_shift, app_key_info.n_neurons,
                master_pop_table_region)
            return block_addr, index

        # Write a matrix for the whole application vertex
        block_addr = self._write_pop_table_padding(spec, block_addr)
        index = self.__poptable_type.update_master_population_table(
            spec, block_addr, max_words, app_key_info.key_and_mask,
            app_key_info.core_mask, app_key_info.core_shift,
            app_key_info.n_neurons, master_pop_table_region)
        # Implicit assumption that no machine-level row_data is ever empty;
        # this must be true in the current code, because the row length is
        # fixed for all synaptic matrices from the same source application
        # vertex
        for _, pre_slice, row_data in matrix_data:
            spec.write_array(row_data)
            n_rows = pre_slice.n_atoms * n_ranges
            block_addr = block_addr + (max_bytes * n_rows)
            if block_addr > all_syn_block_sz:
                raise Exception(
                    "Too much synaptic memory has been written: {} of {} "
                    .format(block_addr, all_syn_block_sz))
        return block_addr, index

    def __write_machine_matrix(
            self, block_addr, single_addr, spec, master_pop_table_region,
            max_synapses, max_words, r_info, row_data, synapse_info, pre_slice,
            post_vertex_slice, single_synapses, all_syn_block_sz, is_delayed):
        # If there are no synapses, don't write anything
        if max_synapses == 0:
            index = None
            # If there is routing information, write an invalid entry
            if r_info is not None:
                index = self.__poptable_type.add_invalid_entry(
                    spec, r_info.first_key_and_mask, 0, 0, 0,
                    master_pop_table_region)
            return block_addr, single_addr, index

        # Write a matrix for an incoming machine vertex
        if max_synapses == 1 and self.__is_direct(
                single_addr, synapse_info, pre_slice, post_vertex_slice,
                is_delayed):
            single_rows = row_data.reshape(-1, 4)[:, 3]
            index = self.__poptable_type.update_master_population_table(
                spec, single_addr, max_words,
                r_info.first_key_and_mask, 0, 0, 0, master_pop_table_region,
                is_single=True)
            single_synapses.append(single_rows)
            single_addr = single_addr + (len(single_rows) * 4)
        else:
            block_addr = self._write_pop_table_padding(spec, block_addr)
            index = self.__poptable_type.update_master_population_table(
                spec, block_addr, max_words,
                r_info.first_key_and_mask, 0, 0, 0, master_pop_table_region)
            spec.write_array(row_data)
            block_addr = block_addr + (len(row_data) * 4)
            if block_addr > all_syn_block_sz:
                raise Exception(
                    "Too much synaptic memory has been written: {} of {} "
                    .format(block_addr, all_syn_block_sz))
        return block_addr, single_addr, index

    def __check_keys_adjacent(self, keys, mask, mask_size):
        # Check that keys are all adjacent
        key_increment = (1 << mask_size)
        last_key = None
        last_slice = None
        for i, (key, v_slice) in enumerate(keys):
            if last_key is None:
                last_key = key
                last_slice = v_slice
            elif (last_key + key_increment) != key:
                return False
            elif (i + 1) < len(keys) and last_slice.n_atoms != v_slice.n_atoms:
                return False
            elif (last_slice.hi_atom + 1) != v_slice.lo_atom:
                return False
            last_key = key
            last_slice = v_slice
        return True

    def __get_app_key_and_mask(self, keys, mask, n_stages, key_space_tracker):

        # Can be merged only if keys are adjacent outside the mask
        keys = sorted(keys, key=lambda item: item[0])
        mask_size = KeySpaceTracker.count_trailing_0s(mask)
        if not self.__check_keys_adjacent(keys, mask, mask_size):
            return None

        # Get the key as the first key and the mask as the mask that covers
        # enough keys
        key = keys[0][0]
        n_extra_mask_bits = int(math.ceil(math.log(len(keys), 2)))
        core_mask = (((2 ** n_extra_mask_bits) - 1))
        new_mask = mask & ~(core_mask << mask_size)

        # Final check because adjacent keys don't mean they all fit under a
        # single mask
        if key & new_mask != key:
            return None

        # Check that the key doesn't cover other keys that it shouldn't
        next_key = keys[-1][0] + (2 ** mask_size)
        max_key = key + (2 ** (mask_size + n_extra_mask_bits))
        n_unused = max_key - (next_key & mask)
        if n_unused > 0 and key_space_tracker.is_allocated(next_key, n_unused):
            return None

        return _AppKeyInfo(key, new_mask, core_mask, mask_size,
                           keys[0][1].n_atoms * n_stages)

    def __app_key_and_mask(self, graph_mapper, m_edges, routing_info,
                           key_space_tracker):
        # Work out if the keys allow the machine vertices to be merged
        mask = None
        keys = list()

        # Can be merged only of all the masks are the same
        for m_edge in m_edges:
            rinfo = routing_info.get_routing_info_for_edge(m_edge)
            vertex_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            if rinfo is None:
                return None
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, vertex_slice))

        if mask is None:
            return None

        return self.__get_app_key_and_mask(keys, mask, 1, key_space_tracker)

    def __delay_app_key_and_mask(self, graph_mapper, m_edges, app_edge,
                                 key_space_tracker):
        # Work out if the keys allow the machine vertices to be
        # merged
        mask = None
        keys = list()

        # Can be merged only of all the masks are the same
        for m_edge in m_edges:
            pre_vertex_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            delay_info_key = (app_edge.pre_vertex, pre_vertex_slice.lo_atom,
                              pre_vertex_slice.hi_atom)
            rinfo = self.__delay_key_index.get(delay_info_key, None)
            if rinfo is None:
                return None
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, pre_vertex_slice))

        return self.__get_app_key_and_mask(keys, mask, app_edge.n_delay_stages,
                                           key_space_tracker)

    def __write_on_chip_matrix_data(
            self, m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
            post_slice_index, post_vertex_slice, app_edge, machine_time_step,
            app_key_info, delay_app_key_info, block_addr, spec,
            master_pop_table_region, all_syn_block_sz, generator_data,
            routing_info):
        # Write the data to generate a matrix on-chip
        max_row_info = self._get_max_row_info(
            synapse_info, post_vertex_slice, app_edge, machine_time_step)
        is_undelayed = bool(max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(max_row_info.delayed_max_n_synapses)

        index = None
        d_index = None

        # Create initial master population table entries if a single
        # matrix is to be created for the whole application vertex
        syn_block_addr = 0xFFFFFFFF
        if is_undelayed and app_key_info is not None:
            block_addr, syn_block_addr, index = self.__reserve_mpop_block(
                block_addr, spec, master_pop_table_region,
                max_row_info.undelayed_max_bytes,
                max_row_info.undelayed_max_words, app_key_info,
                all_syn_block_sz, app_edge.pre_vertex.n_atoms)
            syn_max_addr = block_addr
        elif app_key_info is not None:
            index = self._poptable_type.add_invalid_entry(
                spec, app_key_info.key_and_mask, app_key_info.core_mask,
                app_key_info.core_shift, app_key_info.n_neurons,
                master_pop_table_region)
        delay_block_addr = 0xFFFFFFFF
        if is_delayed and delay_app_key_info is not None:
            block_addr, delay_block_addr, d_index = self.__reserve_mpop_block(
                block_addr, spec, master_pop_table_region,
                max_row_info.delayed_max_bytes, max_row_info.delayed_max_words,
                delay_app_key_info, all_syn_block_sz,
                app_edge.pre_vertex.n_atoms * app_edge.n_delay_stages)
            delay_max_addr = block_addr
        elif delay_app_key_info is not None:
            index = self._poptable_type.add_invalid_entry(
                spec, delay_app_key_info.key_and_mask,
                delay_app_key_info.core_mask, delay_app_key_info.core_shift,
                delay_app_key_info.n_neurons, master_pop_table_region)

        for m_edge in m_edges:
            syn_mat_offset = syn_block_addr
            d_mat_offset = delay_block_addr
            pre_idx = graph_mapper.get_machine_vertex_index(m_edge.pre_vertex)
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)

            # Write the information needed to generate delays
            self.__write_on_chip_delay_data(
                max_row_info, app_edge, pre_slices, pre_idx, post_slices,
                post_slice_index, pre_slice, post_vertex_slice, synapse_info,
                machine_time_step)

            if is_undelayed and app_key_info is not None:
                # If there is a single matrix for the app vertex, jump over the
                # matrix and any padding space
                syn_block_addr = self.__next_app_syn_block_addr(
                    syn_block_addr, pre_slice.n_atoms,
                    max_row_info.undelayed_max_bytes, syn_max_addr)
            elif app_key_info is None:
                # If there isn't a single matrix, add master population table
                # entries for each incoming machine vertex
                r_info = routing_info.get_routing_info_for_edge(m_edge)
                tmp_index = None
                if is_undelayed:
                    m_key_info = _AppKeyInfo(
                        r_info.first_key, r_info.first_mask, 0, 0, 0)
                    block_addr, syn_mat_offset, tmp_index = self.__reserve_mpop_block(
                        block_addr, spec, master_pop_table_region,
                        max_row_info.undelayed_max_bytes,
                        max_row_info.undelayed_max_words, m_key_info,
                        all_syn_block_sz, pre_slice.n_atoms)

                elif r_info is not None:
                    tmp_index = self.__poptable_type.add_invalid_entry(
                        spec, r_info.first_key_and_mask, 0, 0, 0,
                        master_pop_table_region)

                if tmp_index is not None:
                    if index is None:
                        index = tmp_index
                    elif index != tmp_index:
                        raise Exception("Population and subpopulation indices do not match")

            # Do the same as the above for delay vertices too
            if is_delayed and delay_app_key_info is not None:
                delay_block_addr = self.__next_app_syn_block_addr(
                    delay_block_addr,
                    pre_slice.n_atoms * app_edge.n_delay_stages,
                    max_row_info.delayed_max_bytes, delay_max_addr)
            elif delay_app_key_info is None:
                delay_key = (app_edge.pre_vertex, pre_slice.lo_atom,
                             pre_slice.hi_atom)
                r_info = self.__delay_key_index.get(delay_key, None)
                tmp_d_index = None
                if is_delayed:
                    m_key_info = _AppKeyInfo(
                        r_info.first_key, r_info.first_mask, 0, 0, 0)
                    block_addr, d_mat_offset, tmp_d_index = self.__reserve_mpop_block(
                        block_addr, spec, master_pop_table_region,
                        max_row_info.delayed_max_bytes,
                        max_row_info.delayed_max_words, m_key_info,
                        all_syn_block_sz,
                        pre_slice.n_atoms * app_edge.n_delay_stages)
                elif r_info is not None:
                    tmp_d_index = self.__poptable_type.add_invalid_entry(
                        spec, r_info.first_key_and_mask, 0, 0, 0,
                        master_pop_table_region)

                if tmp_d_index is not None:
                    if d_index is None:
                        d_index = tmp_d_index
                    elif d_index != tmp_d_index:
                        raise Exception("Population and subpopulation indices do not match")

            if index is not None and d_index is not None and index != d_index:
                raise Exception("Delay index {} and normal index {} do not match"
                                .format(d_index, index))

            key = (synapse_info, post_vertex_slice.lo_atom)
            self.__synapse_indices[key] = index

            # Create the generator data and note it exists for this post vertex
            generator_data.append(GeneratorData(
                syn_mat_offset, d_mat_offset,
                max_row_info.undelayed_max_words,
                max_row_info.delayed_max_words,
                max_row_info.undelayed_max_n_synapses,
                max_row_info.delayed_max_n_synapses, pre_slices, pre_idx,
                post_slices, post_slice_index, pre_slice, post_vertex_slice,
                synapse_info, app_edge.n_delay_stages + 1, machine_time_step))
            key = (post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)
            self.__gen_on_machine[key] = True
        return block_addr

    def __reserve_mpop_block(
            self, block_addr, spec, master_pop_table_region, max_bytes,
            max_words, app_key_info, all_syn_block_sz, n_rows):
        # Reserve a block in the master population table
        block_addr = self.__poptable_type.get_next_allowed_address(
            block_addr)
        index = self.__poptable_type.update_master_population_table(
            spec, block_addr, max_words, app_key_info.key_and_mask,
            app_key_info.core_mask, app_key_info.core_shift,
            app_key_info.n_neurons, master_pop_table_region)
        syn_block_addr = block_addr
        block_addr += max_bytes * n_rows
        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been reserved: {} of {}".format(
                    block_addr, all_syn_block_sz))
        return block_addr, syn_block_addr, index

    def __next_app_syn_block_addr(
            self, block_addr, n_rows, max_bytes, max_pos):
        # Get the next block address after the sub-table
        block_addr += (max_bytes * n_rows)
        if block_addr > max_pos:
            raise Exception(
                "Too much synaptic memory has been reserved: {} of {}".format(
                    block_addr, max_pos))
        return block_addr

    def __write_on_chip_delay_data(
            self, max_row_info, app_edge, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_info, machine_time_step):
        # If delay edge exists, tell this about the data too, so it can
        # generate its own data
        if (max_row_info.delayed_max_n_synapses > 0 and
                app_edge.delay_edge is not None):
            app_edge.delay_edge.pre_vertex.add_generator_data(
                max_row_info.undelayed_max_n_synapses,
                max_row_info.delayed_max_n_synapses,
                pre_slices, pre_slice_index, post_slices, post_slice_index,
                pre_vertex_slice, post_vertex_slice, synapse_info,
                app_edge.n_delay_stages + 1, machine_time_step)
        elif max_row_info.delayed_max_n_synapses != 0:
            raise Exception(
                "Found delayed items but no delay "
                "machine edge for {}".format(app_edge.label))

    def __get_row_data(
            self, synapse_info, pre_slices, pre_slice_idx, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice, app_edge,
            n_synapse_types, weight_scales, machine_time_step, machine_edge,
            max_row_info):
        (row_data, delayed_row_data, delayed_source_ids,
         delay_stages) = self.__synapse_io.get_synapses(
            synapse_info, pre_slices, pre_slice_idx, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            app_edge.n_delay_stages, n_synapse_types, weight_scales,
            machine_time_step, app_edge, machine_edge, max_row_info)

        if app_edge.delay_edge is not None:
            app_edge.delay_edge.pre_vertex.add_delays(
                pre_vertex_slice, delayed_source_ids, delay_stages)
        elif delayed_source_ids.size != 0:
            raise Exception(
                "Found delayed source IDs but no delay "
                "machine edge for {}".format(app_edge.label))

        if (app_edge, synapse_info) in self.__pre_run_connection_holders:
            for conn_holder in self.__pre_run_connection_holders[
                    app_edge, synapse_info]:
                conn_holder.add_connections(self._read_synapses(
                    synapse_info, pre_vertex_slice, post_vertex_slice,
                    max_row_info.undelayed_max_words,
                    max_row_info.delayed_max_words, n_synapse_types,
                    weight_scales, row_data, delayed_row_data,
                    app_edge.n_delay_stages, machine_time_step))
                conn_holder.finish()

        return (row_data, delayed_row_data)

    def __is_direct(
            self, single_addr, s_info, pre_vertex_slice, post_vertex_slice,
            is_delayed):
        """ Determine if the given connection can be done with a "direct"\
            synaptic matrix - this must have an exactly 1 entry per row
        """
        return (
            not is_delayed and
            isinstance(s_info.connector, OneToOneConnector) and
            isinstance(s_info.synapse_dynamics, SynapseDynamicsStatic) and
            (single_addr + (pre_vertex_slice.n_atoms * 4) <=
                self.__one_to_one_connection_dtcm_max_bytes) and
            (pre_vertex_slice.lo_atom == post_vertex_slice.lo_atom) and
            (pre_vertex_slice.hi_atom == post_vertex_slice.hi_atom))

    def __write_row_data(
            self, spec, connector, pre_vertex_slice, post_vertex_slice,
            row_length, row_data, rinfo, single_synapses,
            master_pop_table_region, synaptic_matrix_region,
            block_addr, single_addr, app_edge):
        if row_length == 1 and self.__is_direct(
                single_addr, connector, pre_vertex_slice, post_vertex_slice,
                app_edge):
            single_rows = row_data.reshape(-1, 4)[:, 3]
            single_synapses.append(single_rows)
            index = self.__poptable_type.update_master_population_table(
                spec, single_addr, 1, rinfo.first_key_and_mask,
                master_pop_table_region, is_single=True)
            single_addr += len(single_rows) * 4
        else:
            block_addr = self._write_padding(
                spec, synaptic_matrix_region, block_addr)
            spec.switch_write_focus(synaptic_matrix_region)
            spec.write_array(row_data)
            index = self.__poptable_type.update_master_population_table(
                spec, block_addr, row_length,
                rinfo.first_key_and_mask, master_pop_table_region)
            block_addr += len(row_data) * 4
        return block_addr, single_addr, index

    def _get_ring_buffer_shifts(
            self, application_vertex, application_graph, machine_timestep):
        """ Get the ring buffer shifts for this vertex
        """
        if self.__ring_buffer_shifts is None:
            self.__ring_buffer_shifts = \
                self._get_ring_buffer_to_input_left_shifts(
                    application_vertex, application_graph, machine_timestep)
        return self.__ring_buffer_shifts

    def _write_synapse_parameters(
            self, spec, vertex_slice, application_graph, machine_time_step, index):

        n_atoms = vertex_slice.n_atoms
        spec.comment("\nWriting Synapse Parameters for {} Neurons:\n".format(
            n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)

        # Write the number of neurons
        spec.write_value(data=n_atoms)

        # Write the number of synapse types managed
        spec.write_value(data=self._implemented_synapse_types)

        # Write the size of the incoming spike buffer
        spec.write_value(data=self._incoming_spike_buffer_size)

        # Write the synapse index for SDRAM offset for synaptic contributions
        spec.write_value(data=self._synapse_index)

        # Write the SDRAM tag for the contribution area
        spec.write_value(data=index)

        # Write the offset for SDRAM (CHECK FOR DUAL EXC SYN TYPES)
        if self._synapse_index > 0:
            spec.write_value(data=self._synapse_index)
        else:
            spec.write_value(data=self.__partition)

        # Hardcoded and moved in the constructor
        #ring_buffer_shifts = self._get_ring_buffer_shifts(
        #    self, application_graph, machine_time_step)

        # Number of variables that can be recorded
        spec.write_value(len(self.RECORDABLES))

        # Check if we are recording something
        recording = False
        for v in self.RECORDABLES:
            if self.is_recording_synapses(v):
                recording = True

        # Tell the core if we are recording
        if recording:
            spec.write_value(1)
        else:
            spec.write_value(0)

        spec.write_array(self._ring_buffer_shifts)

        # Recording data in global parameters
        recording_data = self.__synapse_recorder.get_data(vertex_slice)
        spec.write_array(recording_data)

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "application_graph": "MemoryApplicationGraph",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "placements": "MemoryPlacements",
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "application_graph", "machine_graph", "routing_info",
            "data_n_time_steps", "placements",
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, application_graph, machine_graph, routing_info,
            data_n_time_steps, placements):

        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        # Create an index of delay keys into this vertex
        for m_edge in machine_graph.get_edges_ending_at_vertex(vertex):
            app_edge = graph_mapper.get_application_edge(m_edge)
            if isinstance(app_edge.pre_vertex, DelayExtensionVertex):
                pre_vertex_slice = graph_mapper.get_slice(
                    m_edge.pre_vertex)
                self.__delay_key_index[app_edge.pre_vertex.source_vertex,
                                       pre_vertex_slice.lo_atom,
                                       pre_vertex_slice.hi_atom] = \
                    routing_info.get_routing_info_for_edge(m_edge)

        spec.comment("\n*** Synapses spec block ***\n")

        in_edges = application_graph.get_edges_ending_at_vertex(self)

        all_syn_block_sz = self._get_synaptic_blocks_size(
            vertex_slice, in_edges, machine_time_step)

        # Reserve memory regions
        self._reserve_memory_regions(
            spec, vertex, vertex_slice, machine_graph,
            all_syn_block_sz, graph_mapper)

        # Write the setup region
        spec.switch_write_focus(
            constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # Write the recording region
        spec.switch_write_focus(
            constants.POPULATION_BASED_REGIONS.RECORDING.value)
        spec.write_array(recording_utilities.get_recording_header_array(
            self._get_buffered_sdram(vertex_slice, data_n_time_steps)
        ))

        if vertex.vertex_index is None:
            for c in vertex.constraints:
                if isinstance(c, SameChipAsConstraint) and isinstance(c.vertex, PopulationMachineVertex):
                    vertex.vertex_index = c.vertex.vertex_index

        self._write_synapse_parameters(
            spec, vertex_slice, application_graph, machine_time_step,
            vertex.vertex_index)

        scales = numpy.array([
            self._get_weight_scale(r) * self._weight_scale
            for r in self._ring_buffer_shifts])

        # post_slices = graph_mapper.get_slices(self)
        post_slices = list()
        for v in self._slice_list:
            post_slices.extend(graph_mapper.get_slices(v))

        post_slice_idx = self._slice_list.index(self)

        gen_data = self._write_synaptic_matrix_and_master_population_table(
            spec, post_slices, post_slice_idx, vertex,
            vertex_slice, all_syn_block_sz, scales,
            POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            POPULATION_BASED_REGIONS.DIRECT_MATRIX.value,
            routing_info, graph_mapper, machine_graph, machine_time_step)

        if isinstance(self.__synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            self.__synapse_dynamics.write_parameters(
                spec,
                POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                machine_time_step, scales,
                application_graph=application_graph,
                machine_graph=machine_graph,
                app_vertex=self, post_slice=vertex_slice,
                machine_vertex=vertex,
                graph_mapper=graph_mapper, routing_info=routing_info)
        else:
            self.__synapse_dynamics.write_parameters(
                spec,
                POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                machine_time_step, scales)

        self.__weight_scales[placement] = scales

        self._write_on_machine_data_spec(
            spec, vertex_slice, scales, gen_data)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self._n_profile_samples)

        # End the writing of this specification
        spec.end_specification()

    def clear_connection_cache(self):
        self.__retrieved_blocks = dict()

    def get_connections_from_machine(
            self, transceiver, placement, machine_edge, graph_mapper,
            routing_infos, synapse_info, machine_time_step,
            using_extra_monitor_cores, placements=None, monitor_api=None,
            monitor_placement=None, monitor_cores=None,
            handle_time_out_configuration=True, fixed_routes=None):
        app_edge = graph_mapper.get_application_edge(machine_edge)
        if not isinstance(app_edge, ProjectionApplicationEdge):
            return None

        # Get details for extraction
        pre_vertex_slice = graph_mapper.get_slice(machine_edge.pre_vertex)
        post_vertex_slice = graph_mapper.get_slice(machine_edge.post_vertex)

        # Get the key for the pre_vertex
        key = routing_infos.get_first_key_for_edge(machine_edge)

        # Get the key for the delayed pre_vertex
        delayed_key = None
        if app_edge.delay_edge is not None:
            delayed_key = self.__delay_key_index[
                app_edge.pre_vertex, pre_vertex_slice.lo_atom,
                pre_vertex_slice.hi_atom].first_key

        # Get the block for the connections from the pre_vertex
        synapse_key = (synapse_info,
                       post_vertex_slice.lo_atom)
        index = self.__synapse_indices[synapse_key]
        master_pop_table, direct_synapses, indirect_synapses = \
            self.__compute_addresses(transceiver, placement)
        data, max_row_length = self._retrieve_synaptic_block(
            transceiver, placement, master_pop_table, indirect_synapses,
            direct_synapses, key, pre_vertex_slice.n_atoms, index,
            using_extra_monitor_cores, placements, monitor_api,
            monitor_placement, monitor_cores, fixed_routes)

        # Get the block for the connections from the delayed pre_vertex
        delayed_data = None
        delayed_max_row_len = 0
        if delayed_key is not None:
            delayed_data, delayed_max_row_len = self._retrieve_synaptic_block(
                transceiver, placement, master_pop_table, indirect_synapses,
                direct_synapses, delayed_key,
                pre_vertex_slice.n_atoms * app_edge.n_delay_stages,
                index, using_extra_monitor_cores, placements,
                monitor_api, monitor_placement, monitor_cores,
                handle_time_out_configuration, fixed_routes)

        # Convert the blocks into connections
        return self._read_synapses(
            synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_len, self._implemented_synapse_types,
            self.__weight_scales[placement], data, delayed_data,
            app_edge.n_delay_stages, machine_time_step)

    def __compute_addresses(self, transceiver, placement):
        """ Helper for computing the addresses of the master pop table and\
            synaptic-matrix-related bits.
        """
        master_pop_table = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            transceiver)
        synaptic_matrix = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            transceiver)
        direct_synapses = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.DIRECT_MATRIX.value,
            transceiver) + 4
        return master_pop_table, direct_synapses, synaptic_matrix

    def _extract_synaptic_matrix_data_location(
            self, key, master_pop_table_address, transceiver, placement):
        return self.__poptable_type.extract_synaptic_matrix_data_location(
            key, master_pop_table_address, transceiver,
            placement.x, placement.y)

    def _read_synapses(self, info, pre_slice, post_slice, len1, len2, len3,
                       weight_scales, data1, data2, n_delays, timestep):
        return self.__synapse_io.read_synapses(
            info, pre_slice, post_slice, len1, len2, len3, weight_scales,
            data1, data2, n_delays, timestep)

    def _retrieve_synaptic_block(
            self, txrx, placement, master_pop_table_address,
            indirect_synapses_address, direct_synapses_address,
            key, n_rows, index, using_monitors, placements=None,
            monitor_api=None, monitor_placement=None, monitor_cores=None,
            handle_time_out_configuration=True, fixed_routes=None):
        """ Read in a synaptic block from a given processor and vertex on\
            the machine
        """
        # See if we have already got this block
        if (placement, key, index) in self.__retrieved_blocks:
            return self.__retrieved_blocks[placement, key, index]

        items = self._extract_synaptic_matrix_data_location(
            key, master_pop_table_address, txrx, placement)
        if index >= len(items):
            return None, None

        max_row_length, synaptic_block_offset, is_single = items[index]
        if max_row_length == 0:
            return None, None

        block = None
        if max_row_length > 0 and synaptic_block_offset is not None:
            # if exploiting the extra monitor cores, need to set the machine
            # for data extraction mode
            if using_monitors and handle_time_out_configuration:
                monitor_api.set_cores_for_data_streaming(
                    txrx, monitor_cores, placements)

            # read in the synaptic block
            if not is_single:
                block = self.__read_multiple_synaptic_blocks(
                    txrx, monitor_api, placement, n_rows, max_row_length,
                    indirect_synapses_address + synaptic_block_offset,
                    using_monitors, monitor_placement, fixed_routes)
            else:
                block, max_row_length = self.__read_single_synaptic_block(
                    txrx, monitor_api, placement, n_rows,
                    direct_synapses_address + synaptic_block_offset,
                    using_monitors, monitor_placement, fixed_routes)

            if using_monitors and handle_time_out_configuration:
                monitor_api.unset_cores_for_data_streaming(
                    txrx, monitor_cores, placements)

        self.__retrieved_blocks[placement, key, index] = \
            (block, max_row_length)
        return block, max_row_length

    def __read_multiple_synaptic_blocks(
            self, transceiver, monitor_api, placement, n_rows, max_row_length,
            address, using_monitors, monitor_placement, fixed_routes):
        """ Read in an array of synaptic blocks.
        """
        # calculate the synaptic block size in bytes
        synaptic_block_size = self.__synapse_io.get_block_n_bytes(
            max_row_length, n_rows)

        # read in the synaptic block
        if using_monitors:
            return monitor_api.get_data(
                monitor_placement, address, synaptic_block_size, fixed_routes)
        return transceiver.read_memory(
            placement.x, placement.y, address, synaptic_block_size)

    def __read_single_synaptic_block(
            self, transceiver, data_receiver, placement, n_rows, address,
            using_monitors, monitor_placement, fixed_routes):
        """ Read in a single synaptic block.
        """
        # The data is one per row
        synaptic_block_size = n_rows * 4

        # read in the synaptic row data
        if using_monitors:
            single_block = data_receiver.get_data(
                monitor_placement, address, synaptic_block_size, fixed_routes)
        else:
            single_block = transceiver.read_memory(
                placement.x, placement.y, address, synaptic_block_size)

        # Convert the block into a set of rows
        numpy_block = numpy.zeros((n_rows, 4), dtype="uint32")
        numpy_block[:, 3] = numpy.asarray(
            single_block, dtype="uint8").view("uint32")
        numpy_block[:, 1] = 1
        return bytearray(numpy_block.tobytes()), 1

    # inherited from AbstractProvidesIncomingPartitionConstraints
    @overrides(AbstractProvidesIncomingPartitionConstraints.
               get_incoming_partition_constraints)
    def get_incoming_partition_constraints(self, partition):
        return self.__poptable_type.get_edge_constraints()

    def _write_on_machine_data_spec(
            self, spec, post_vertex_slice, weight_scales, generator_data):
        """ Write the data spec for the synapse expander

        :param spec: The specification to write to
        :param post_vertex_slice: The slice of the vertex being written
        :param weight_scales: scaling of weights on each synapse
        """
        if not generator_data:
            return

        if len(weight_scales) < self._model_synapse_types:
            tmp_weight_scales = list()
            for i in range(self._model_synapse_types):
                if i != self._synapse_index:
                    tmp_weight_scales.append(0)
                else:
                    # ADAPT THIS FOR MULTIPLE EXCITATORY TYPES
                    # AS THE SYNAPSE INDEX
                    tmp_weight_scales.append(weight_scales[0])

        n_bytes = (
            _SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self._implemented_synapse_types * 4))
        for data in generator_data:
            n_bytes += data.size

        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value,
            size=n_bytes, label="ConnectorBuilderRegion")
        spec.switch_write_focus(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value)

        spec.write_value(len(generator_data))
        spec.write_value(post_vertex_slice.lo_atom)
        spec.write_value(post_vertex_slice.n_atoms)
        spec.write_value(self._model_synapse_types)
        spec.write_value(get_n_bits(self._implemented_synapse_types))
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        spec.write_value(n_neuron_id_bits)
        for w in tmp_weight_scales:
            spec.write_value(int(w), data_type=DataType.INT32)

        for data in generator_data:
            spec.write_array(data.gen_data)

    def gen_on_machine(self, vertex_slice):
        """ True if the synapses should be generated on the machine
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        return self.__gen_on_machine.get(key, False)

    def _get_buffered_sdram(self, vertex_slice, n_machine_time_steps):
        values = list()
        for variable in self.RECORDABLES:
            values.append(
                self.__synapse_recorder.get_buffered_sdram(
                    variable, vertex_slice, n_machine_time_steps))
        return values

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):

        vertex = SynapseMachineVertex(
            resources_required, self.__synapse_recorder.recorded_region_ids,
            label, constraints)

        self._machine_vertices[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)] = vertex
        SynapticManager._n_vertices += 1

        for app_vertex in self._connected_app_vertices:
            out_vertex =\
                app_vertex.get_machine_vertex_at((vertex_slice.hi_atom - self._atoms_offset) // self._atoms_neuron_cores)
            if out_vertex is not None:
                vertex.add_constraint(SameChipAsConstraint(out_vertex))

        # return machine vertex
        return vertex

    @overrides(AbstractSynapseRecordable.set_synapse_recording)
    def set_synapse_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        self.__change_requires_mapping = not self.is_recording_synapses(variable)
        self.__synapse_recorder.set_recording(variable, new_state, sampling_interval, indexes)

    @overrides(AbstractSynapseRecordable.get_synapse_data)
    def get_synapse_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        # CHECK THAT 0 IS CORRECT AS INDEX!!
        return self._synapse_recorder.get_matrix_data(
            self.label, buffer_manager, 0, placements, graph_mapper,
            self, variable, n_machine_time_steps)

    @overrides(AbstractSynapseRecordable.get_synapse_recordable_variables)
    def get_synapse_recordable_variables(self):
        return self.__synapse_recorder.get_recordable_variables()

    @overrides(AbstractSynapseRecordable.is_recording_synapses)
    def is_recording_synapses(self, variable):
        return self.__synapse_recorder.is_recording(variable)

    @overrides(AbstractSynapseRecordable.get_synapse_sampling_interval)
    def get_synapse_sampling_interval(self, variable):
        return self.__synapse_recorder.get_synapse_sampling_interval(variable)

    @overrides(AbstractSynapseRecordable.clear_synapse_recording)
    def clear_synapse_recording(self, variable, buffer_manager, placements,
                                graph_mapper):
        # CHECK THAT 0 IS CORRECT!
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper, 0)

    def _clear_recording_region(
            self, buffer_manager, placements, graph_mapper,
            recording_region_id):
        """ Clear a recorded data region from the buffer manager.
        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :param recording_region_id: the recorded region ID for clearing
        :rtype: None
        """
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p, recording_region_id)

    def get_units(self, variable):
        if variable in self.RECORDABLES:
            return self._synapse_recorder.get_recordable_units(variable)
        raise Exception("Population does not have parameter {}".format(variable))

    def get_machine_vertex_at(self, low, high):

        vertices = list()

        for (lo, hi) in self._machine_vertices:
            if lo >= low and hi <= high:
                vertices.append(self._machine_vertices[(lo, hi)])

        return vertices


class _AppKeyInfo(object):

    __slots__ = ["app_key", "app_mask", "core_mask", "core_shift", "n_neurons"]

    def __init__(self, app_key, app_mask, core_mask, core_shift, n_neurons):
        self.app_key = app_key
        self.app_mask = app_mask
        self.core_mask = core_mask
        self.core_shift = core_shift
        self.n_neurons = n_neurons

    @property
    def key_and_mask(self):
        return BaseKeyAndMask(self.app_key, self.app_mask)
