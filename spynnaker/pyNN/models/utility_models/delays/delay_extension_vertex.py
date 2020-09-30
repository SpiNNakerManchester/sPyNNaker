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

from collections import defaultdict
import logging
import math

from spinn_front_end_common.abstract_models.impl.\
    tdma_aware_application_vertex import TDMAAwareApplicationVertex
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.model.constraints.partitioner_constraints import (
    SameAtomsAsVertexConstraint)
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification,
    AbstractProvidesOutgoingPartitionConstraints)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    SIMULATION_N_BYTES, BITS_PER_WORD, BYTES_PER_WORD)
from .delay_block import DelayBlock
from .delay_extension_machine_vertex import DelayExtensionMachineVertex
from .delay_generator_data import DelayGeneratorData
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

logger = logging.getLogger(__name__)

#  1. has_key 2. key 3. incoming_key 4. incoming_mask 5. n_atoms
#  6. n_delay_stages
_DELAY_PARAM_HEADER_WORDS = 6
# pylint: disable=protected-access
_DELEXT_REGIONS = DelayExtensionMachineVertex._DELAY_EXTENSION_REGIONS
_EXPANDER_BASE_PARAMS_SIZE = 3 * BYTES_PER_WORD

# The microseconds per timestep will be divided by this for the max offset
_MAX_OFFSET_DENOMINATOR = 10


class DelayExtensionVertex(
        TDMAAwareApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractProvidesOutgoingPartitionConstraints):
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
        "__time_scale_factor",
        "__delay_generator_data",
        "__n_data_specs"]

    MAX_DELAY_BLOCKS = 8
    MAX_TIMER_TICS_SUPPORTED_PER_BLOCK = 16

    MAX_SUPPORTED_DELAY_IN_TICKS = (
        MAX_DELAY_BLOCKS * MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)

    # The maximum delay supported by the Delay extension, in ticks.

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, time_scale_factor, constraints=None,
                 label="DelayExtension"):
        """
        :param int n_neurons: the number of neurons
        :param int delay_per_stage: the delay per stage
        :param ~pacman.model.graphs.application.ApplicationVertex \
                source_vertex:
            where messages are coming from
        :param int machine_time_step: how long is the machine time step
        :param int time_scale_factor: what slowdown factor has been applied
        :param iterable(~pacman.model.constraints.AbstractConstraint) \
                constraints:
            the vertex constraints
        :param str label: the vertex label
        """
        # pylint: disable=too-many-arguments
        TDMAAwareApplicationVertex.__init__(self, label, constraints, 256)

        self.__source_vertex = source_vertex
        self.__n_delay_stages = 0
        self.__delay_per_stage = delay_per_stage
        self.__delay_generator_data = defaultdict(list)
        self.__machine_time_step = machine_time_step
        self.__time_scale_factor = time_scale_factor
        self.__n_data_specs = 0

        # atom store
        self.__n_atoms = n_neurons

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        self.add_constraint(
            SameAtomsAsVertexConstraint(source_vertex))

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection\
            out of this delay extension vertex

        :rtype: int
        """
        return self.__n_delay_stages

    @n_delay_stages.setter
    def n_delay_stages(self, n_delay_stages):
        self.__n_delay_stages = n_delay_stages

    @property
    def source_vertex(self):
        """
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self.__source_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param list(int) source_ids:
        :param list(int) stages:
        """
        if vertex_slice not in self.__delay_blocks:
            self.__delay_blocks[vertex_slice] = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        for (source_id, stage) in zip(source_ids, stages):
            self.__delay_blocks[vertex_slice].add_delay(source_id, stage)

    def add_generator_data(
            self, max_row_n_synapses, max_delayed_row_n_synapses,
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_information,
            max_stage, machine_time_step):
        """ Add delays for a connection to be generated

        :param int max_row_n_synapses:
        :param int max_delayed_row_n_synapses:
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
        :param int pre_slice_index:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param int post_slice_index:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ~spynnaker.pyNN.models.neural_projections.SynapseInformation \
                synapse_information:
        :param int max_stage:
        :param int machine_time_step:
        """
        self.__delay_generator_data[pre_vertex_slice].append(
            DelayGeneratorData(
                max_row_n_synapses, max_delayed_row_n_synapses,
                pre_slices, pre_slice_index, post_slices, post_slice_index,
                pre_vertex_slice, post_vertex_slice,
                synapse_information, max_stage, machine_time_step))

    @inject_items({
        "machine_graph": "MemoryMachineGraph",
        "routing_infos": "MemoryRoutingInfos"})
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={"machine_graph", "routing_infos"})
    def generate_data_specification(
            self, spec, placement, machine_graph, routing_infos):
        """
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        """
        # pylint: disable=arguments-differ

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = vertex.vertex_slice
        n_words_per_stage = int(
            math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        delay_params_sz = BYTES_PER_WORD * (
            _DELAY_PARAM_HEADER_WORDS +
            (self.__n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.SYSTEM.value,
            size=SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.TDMA_REGION.value,
            size=self.tdma_sdram_size_in_bytes, label="tdma data")

        # reserve region for provenance
        vertex.reserve_provenance_data_region(spec)

        self._write_setup_info(
            spec, self.__machine_time_step, self.__time_scale_factor,
            vertex.get_binary_file_name())

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)

        incoming_key = 0
        incoming_mask = 0
        incoming_edges = machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = incoming_edge.pre_vertex.vertex_slice
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                r_info = routing_infos.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask)

        if vertex_slice in self.__delay_generator_data:
            generator_data = self.__delay_generator_data[vertex_slice]
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

        # add tdma data
        spec.switch_write_focus(_DELEXT_REGIONS.TDMA_REGION.value)
        spec.write_array(self.generate_tdma_data_specification_data(
            self.vertex_slices.index(vertex_slice)))

        # End-of-Spec:
        spec.end_specification()

    def _write_setup_info(
            self, spec, machine_time_step, time_scale_factor, binary_name):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param int machine_time_step:v the machine time step
        :param int time_scale_factor: the time scale factor
        :param str binary_name: the binary name
        """
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(_DELEXT_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            binary_name, machine_time_step, time_scale_factor))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask):
        """ Generate Delay Parameter data

        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int key:
        :param int incoming_key:
        :param int incoming_mask:
        """
        # pylint: disable=too-many-arguments

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(_DELEXT_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        if key is None:
            spec.write_value(0)
            spec.write_value(0)
        else:
            spec.write_value(1)
            spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self.__n_delay_stages)

        # Write the actual delay blocks (create a new one if it doesn't exist)
        if vertex_slice in self.__delay_blocks:
            delay_block = self.__delay_blocks[vertex_slice]
        else:
            delay_block = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        spec.write_array(array_values=delay_block.delay_block)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    def gen_on_machine(self, vertex_slice):
        """ Determine if the given slice needs to be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        return vertex_slice in self.__delay_generator_data
