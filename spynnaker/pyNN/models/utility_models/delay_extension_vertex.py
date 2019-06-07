try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
import logging
import math
import sys
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.model.constraints.partitioner_constraints import (
    SameAtomsAsVertexConstraint)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractProvidesNKeysForPartition, AbstractGeneratesDataSpecification,
    AbstractProvidesOutgoingPartitionConstraints, AbstractHasAssociatedBinary)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from .delay_block import DelayBlock
from .delay_extension_machine_vertex import DelayExtensionMachineVertex
from .delay_generator_data import DelayGeneratorData
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.neural_projections import DelayedApplicationEdge
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)

logger = logging.getLogger(__name__)

_DELAY_PARAM_HEADER_WORDS = 8
# pylint: disable=protected-access
_DELEXT_REGIONS = DelayExtensionMachineVertex._DELAY_EXTENSION_REGIONS
_EXPANDER_BASE_PARAMS_SIZE = 3 * 4

# The microseconds per timestep will be divided by this for the max offset
_MAX_OFFSET_DENOMINATOR = 10


class DelayExtensionVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesNKeysForPartition):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """
    __slots__ = [
        "__delay_blocks",
        "__delay_per_stage",
        "__machine_time_step",
        "__n_atoms",
        "__n_delay_stages",
        "__source_vertex",
        "__timescale_factor",
        "__delay_generator_data",
        "__n_subvertices",
        "__n_data_specs"]

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        :param n_neurons: the number of neurons
        :param delay_per_stage: the delay per stage
        :param source_vertex: where messages are coming from
        :param machine_time_step: how long is the machine time step
        :param timescale_factor: what slowdown factor has been applied
        :param constraints: the vertex constraints
        :param label: the vertex label
        """
        # pylint: disable=too-many-arguments
        super(DelayExtensionVertex, self).__init__(label, constraints, 256)

        self.__source_vertex = source_vertex
        self.__n_delay_stages = 0
        self.__delay_per_stage = delay_per_stage
        self.__delay_generator_data = defaultdict(list)
        self.__machine_time_step = machine_time_step
        self.__timescale_factor = timescale_factor
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # atom store
        self.__n_atoms = n_neurons

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        self.add_constraint(
            SameAtomsAsVertexConstraint(source_vertex))

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        self.__n_subvertices += 1
        return DelayExtensionMachineVertex(
            resources_required, label, constraints)

    @inject_items({
        "graph": "MemoryApplicationGraph"})
    @overrides(ApplicationVertex.get_resources_used_by_atoms,
               additional_arguments={"graph"})
    def get_resources_used_by_atoms(self, vertex_slice, graph):
        out_edges = graph.get_edges_starting_at_vertex(self)
        return ResourceContainer(
            sdram=ConstantSDRAM(
                self.get_sdram_usage_for_atoms(out_edges)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)))

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection\
            out of this delay extension vertex
        """
        return self.__n_delay_stages

    @n_delay_stages.setter
    def n_delay_stages(self, n_delay_stages):
        self.__n_delay_stages = n_delay_stages

    @property
    def source_vertex(self):
        return self.__source_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self.__delay_blocks:
            self.__delay_blocks[key] = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        for (source_id, stage) in zip(source_ids, stages):
            self.__delay_blocks[key].add_delay(source_id, stage)

    def add_generator_data(
            self, max_row_n_synapses, max_delayed_row_n_synapses,
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_information,
            max_stage, machine_time_step):
        """ Add delays for a connection to be generated
        """
        key = (pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom)
        self.__delay_generator_data[key].append(
            DelayGeneratorData(
                max_row_n_synapses, max_delayed_row_n_synapses,
                pre_slices, pre_slice_index, post_slices, post_slice_index,
                pre_vertex_slice, post_vertex_slice,
                synapse_information, max_stage, machine_time_step))

    @inject_items({
        "machine_graph": "MemoryMachineGraph",
        "graph_mapper": "MemoryGraphMapper",
        "routing_infos": "MemoryRoutingInfos"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_graph", "graph_mapper", "routing_infos"
        })
    def generate_data_specification(
            self, spec, placement,
            machine_graph, graph_mapper, routing_infos):
        # pylint: disable=too-many-arguments, arguments-differ

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = graph_mapper.get_slice(vertex)
        n_words_per_stage = int(math.ceil(vertex_slice.n_atoms / 32.0))
        delay_params_sz = 4 * (_DELAY_PARAM_HEADER_WORDS +
                               (self.__n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.SYSTEM.value,
            size=SIMULATION_N_BYTES,
            label='setup')

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        vertex.reserve_provenance_data_region(spec)

        self.write_setup_info(
            spec, self.__machine_time_step, self.__timescale_factor)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)

        incoming_key = None
        incoming_mask = None
        incoming_edges = machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = graph_mapper.get_slice(
                incoming_edge.pre_vertex)
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                r_info = routing_infos.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        n_outgoing_edges = len(
            machine_graph.get_edges_starting_at_vertex(vertex))
        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask,
            self.__n_subvertices, self.__machine_time_step,
            self.__timescale_factor, n_outgoing_edges)

        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key in self.__delay_generator_data:
            generator_data = self.__delay_generator_data[key]
            expander_size = sum(data.size for data in generator_data)
            expander_size += _EXPANDER_BASE_PARAMS_SIZE
            spec.reserve_memory_region(
                region=_DELEXT_REGIONS.EXPANDER_REGION.value,
                size=expander_size, label='delay_expander')
            spec.switch_write_focus(_DELEXT_REGIONS.EXPANDER_REGION.value)
            spec.write_value(len(generator_data))
            spec.write_value(vertex_slice.lo_atom)
            spec.write_value(vertex_slice.n_atoms)
            for data in generator_data:
                spec.write_array(data.gen_data)

        # End-of-Spec:
        spec.end_specification()

    def write_setup_info(self, spec, machine_time_step, time_scale_factor):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(_DELEXT_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask,
            total_n_vertices, machine_time_step, time_scale_factor,
            n_outgoing_edges):
        """ Generate Delay Parameter data
        """
        # pylint: disable=too-many-arguments

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(_DELEXT_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self.__n_delay_stages)

        # Write the offset value
        max_offset = (
            machine_time_step * time_scale_factor) // _MAX_OFFSET_DENOMINATOR
        spec.write_value(
            int(math.ceil(max_offset / total_n_vertices)) *
            self.__n_data_specs)
        self.__n_data_specs += 1

        # Write the time between spikes
        spikes_per_timestep = self.__n_delay_stages * vertex_slice.n_atoms
        time_between_spikes = (
            (machine_time_step * time_scale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the number of outgoing edges
        spec.write_value(n_outgoing_edges)

        # Write the actual delay blocks (create a new one if it doesn't exist)
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key in self.__delay_blocks:
            delay_block = self.__delay_blocks[key]
        else:
            delay_block = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        spec.write_array(array_values=delay_block.delay_block)

    def get_cpu_usage_for_atoms(self, vertex_slice):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, out_edges):
        return (SYSTEM_BYTES_REQUIREMENT +
                DelayExtensionMachineVertex.get_provenance_data_size(0) +
                self._get_size_of_generator_information(out_edges))

    def _get_edge_generator_size(self, synapse_info):
        """ Get the size of the generator data for a given synapse info object
        """
        connector = synapse_info.connector
        dynamics = synapse_info.synapse_dynamics
        connector_gen = isinstance(
            connector, AbstractGenerateConnectorOnMachine) and \
            connector.generate_on_machine(
                synapse_info.weight, synapse_info.delay)
        synapse_gen = isinstance(
            dynamics, AbstractGenerateOnMachine)
        if connector_gen and synapse_gen:
            return sum((
                DelayGeneratorData.BASE_SIZE,
                connector.gen_delay_params_size_in_bytes(
                    synapse_info.delay),
                connector.gen_connector_params_size_in_bytes,
            ))
        return 0

    def _get_size_of_generator_information(self, out_edges):
        """ Get the size of the generator data for all edges
        """
        gen_on_machine = False
        size = 0
        for out_edge in out_edges:
            if isinstance(out_edge, DelayedApplicationEdge):
                for synapse_info in out_edge.synapse_information:

                    # Get the number of likely vertices
                    max_atoms = sys.maxsize
                    edge_post_vertex = out_edge.post_vertex
                    if (isinstance(
                            edge_post_vertex, ApplicationVertex)):
                        max_atoms = edge_post_vertex.get_max_atoms_per_core()
                    if out_edge.post_vertex.n_atoms < max_atoms:
                        max_atoms = edge_post_vertex.n_atoms
                    n_edge_vertices = int(math.ceil(
                        float(edge_post_vertex.n_atoms) / float(max_atoms)))

                    # Get the size
                    gen_size = self._get_edge_generator_size(synapse_info)
                    if gen_size > 0:
                        gen_on_machine = True
                        size += gen_size * n_edge_vertices
        if gen_on_machine:
            size += _EXPANDER_BASE_PARAMS_SIZE
        return size

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "delay_extension.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def get_n_keys_for_partition(self, partition, graph_mapper):
        vertex_slice = graph_mapper.get_slice(partition.pre_vertex)
        if self.__n_delay_stages == 0:
            return 1
        return vertex_slice.n_atoms * self.__n_delay_stages

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    def gen_on_machine(self, vertex_slice):
        """ Determine if the given slice needs to be generated on the machine
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        return key in self.__delay_generator_data
