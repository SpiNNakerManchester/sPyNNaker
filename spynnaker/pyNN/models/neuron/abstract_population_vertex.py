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

import logging
import os
import math
import numpy
import random

from spinn_utilities.overrides import overrides

from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.model.graphs.common import Slice

from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractProvidesIncomingPartitionConstraints,
    AbstractProvidesOutgoingPartitionConstraints, AbstractHasAssociatedBinary,
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification,
    AbstractCanReset)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.utilities import (
    constants as common_constants, helpful_functions, globals_variables)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.interface.profiling import profile_utils

from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable, NeuronRecorder)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractPopulationSettable,
    AbstractReadParametersBeforeSet, AbstractContainsUnits)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.ranged import (
    SpynnakerRangeDictionary, SpynnakerRangedList)
from spynnaker.pyNN.models.neural_properties import AbstractIsRateBased
#from spynnaker.pyNN.models.neuron import SynapseMachineVertex

from .population_machine_vertex import PopulationMachineVertex
from spynnaker.pyNN.utilities.running_stats import RunningStats

logger = logging.getLogger(__name__)

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 36
_NEURON_BASE_SDRAM_USAGE_IN_BYTES = 12
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

# TODO: Make sure these values are correct (particularly CPU cycles)
_C_MAIN_BASE_DTCM_USAGE_IN_BYTES = 12
_C_MAIN_BASE_SDRAM_USAGE_IN_BYTES = 72
_C_MAIN_BASE_N_CPU_CYCLES = 0

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10


class AbstractPopulationVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractContainsUnits,
        AbstractSpikeRecordable,  AbstractNeuronRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractChangableAfterRun,
        AbstractRewritesDataSpecification, AbstractReadParametersBeforeSet,
        ProvidesKeyToAtomMappingImpl, AbstractCanReset):
    """ Underlying vertex model for Neural Populations.
    """
    __slots__ = [
        "__change_requires_mapping",
        "__change_requires_neuron_parameters_reload",
        "__change_requires_data_generation",
        "__incoming_spike_buffer_size",
        "__n_atoms",
        "__n_profile_samples",
        "__neuron_impl",
        "__neuron_recorder",
        "_parameters",  # See AbstractPyNNModel
        "__pynn_model",
        "_state_variables",  # See AbstractPyNNModel
        "__synapse_manager",
        "__time_between_requests",
        "__units",
        "_ring_buffer_shifts",
        "_machine_vertices",
        "_connected_app_vertices",
        "__n_subvertices",
        "__n_data_specs",
        "__initial_state_variables",
        "__has_reset_last",
        "__updated_state_variables",
        "_atoms_offset",
        "_slice_list",
        "_incoming_partitions",
        "_n_targets",
        "_current_offset",
        "__max_atoms_per_core"]

    BASIC_MALLOC_USAGE = 2

    # recording region IDs
    SPIKE_RECORDING_REGION = 0

    # the size of the runtime SDP port data region
    RUNTIME_SDP_PORT_SIZE = 4

    # 18 elements before the start of global parameters
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 72

    # The Buffer traffic type
    TRAFFIC_IDENTIFIER = "BufferTraffic"

    _n_vertices = 0

    def __init__(
            self, n_neurons, atoms_offset, label, constraints, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, neuron_impl, pynn_model, n_targets):
        # pylint: disable=too-many-arguments, too-many-locals
        super(AbstractPopulationVertex, self).__init__(
            label, constraints, max_atoms_per_core)

        self.__n_atoms = n_neurons
        self.__n_subvertices = 0
        self.__n_data_specs = 0
        self._atoms_offset = atoms_offset
        self._n_targets = n_targets
        self._current_offset = 0
        self.__max_atoms_per_core = max_atoms_per_core

        # get config from simulator
        config = globals_variables.get_simulator().config

        self.__neuron_impl = neuron_impl
        self.__pynn_model = pynn_model
        self._parameters = SpynnakerRangeDictionary(n_neurons)
        self._state_variables = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_parameters(self._parameters)
        self.__neuron_impl.add_state_variables(self._state_variables)
        #possible remove the ring buffer shif, or just placeholder for rate-based
        self._ring_buffer_shifts = None
        self._machine_vertices = dict()
        self._connected_app_vertices = None
        self._slice_list = None
        self._incoming_partitions = None
        self.__initial_state_variables = None
        self.__updated_state_variables = set()

        # Set up for recording
        recordables = ["spikes"]
        recordables.extend(self.__neuron_impl.get_recordable_variables())
        self.__neuron_recorder = NeuronRecorder(recordables, n_neurons)

        # bool for if state has changed.
        self.__change_requires_mapping = True
        self.__change_requires_neuron_parameters_reload = False
        self.__change_requires_data_generation = False
        self.__has_reset_last = True

        # Set up for profiling
        self.__n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    def _neuron_recorder(self):  # for testing only
        return self.__neuron_recorder

    @property
    def atoms_offset(self):
        return self._atoms_offset

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

        variableSDRAM = self.__neuron_recorder.get_variable_sdram_usage(
            vertex_slice)
        constantSDRAM = ConstantSDRAM(
                self._get_sdram_usage_for_atoms(
                    vertex_slice, graph, machine_time_step))

        # set resources required from this object
        container = ResourceContainer(
            sdram=variableSDRAM + constantSDRAM,
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)))

        # return the total resources.
        return container

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

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

    @property
    def incoming_partitions(self):
        return self._incoming_partitions

    @incoming_partitions.setter
    def incoming_partitions(self, incoming_partitions):
        self._incoming_partitions = incoming_partitions

    @property
    @overrides(AbstractChangableAfterRun.requires_data_generation)
    def requires_data_generation(self):
        return self.__change_requires_data_generation

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False
        self.__change_requires_data_generation = False

    # CB: May be dead code
    def _get_buffered_sdram_per_timestep(self, vertex_slice):
        values = [self.__neuron_recorder.get_buffered_sdram_per_timestep(
                "spikes", vertex_slice)]
        for variable in self.__neuron_impl.get_recordable_variables():
            values.append(
                self.__neuron_recorder.get_buffered_sdram_per_timestep(
                    variable, vertex_slice))
        return values

    def _get_buffered_sdram(self, vertex_slice, n_machine_time_steps):
        values = [self.__neuron_recorder.get_buffered_sdram(
                "spikes", vertex_slice, n_machine_time_steps)]
        for variable in self.__neuron_impl.get_recordable_variables():
            values.append(
                self.__neuron_recorder.get_buffered_sdram(
                    variable, vertex_slice, n_machine_time_steps))
        return values

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):

        # Update the low and high atoms for the slice, transparent to PACMAN
        #vertex_slice.lo_atom += self._atoms_offset
        #vertex_slice.hi_atom += self._atoms_offset

        vertex = PopulationMachineVertex(
            resources_required, self.__neuron_recorder.recorded_region_ids,
            label, sum(self._incoming_partitions), constraints)

        vertex.mem_offset = self._current_offset
        self._current_offset = (self._current_offset + 1) % self._n_targets

        AbstractPopulationVertex._n_vertices += 1
        self._machine_vertices[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)] = vertex

        for app_vertex in self._connected_app_vertices:
            out_vertices =\
                app_vertex.get_machine_vertex_at(
                    vertex_slice.lo_atom, vertex_slice.hi_atom)
            if len(out_vertices)> 0:
                for out_vertex in out_vertices:
                    vertex.add_constraint(SameChipAsConstraint(out_vertex))
        self.__n_subvertices += 1

        return vertex

    def get_cpu_usage_for_atoms(self, vertex_slice):
        return (
            _NEURON_BASE_N_CPU_CYCLES + _C_MAIN_BASE_N_CPU_CYCLES +
            (_NEURON_BASE_N_CPU_CYCLES_PER_NEURON * vertex_slice.n_atoms) +
            self.__neuron_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
            self.__neuron_impl.get_n_cpu_cycles(vertex_slice.n_atoms))

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        return (
            _NEURON_BASE_DTCM_USAGE_IN_BYTES +
            self.__neuron_impl.get_dtcm_usage_in_bytes(vertex_slice.n_atoms) +
            self.__neuron_recorder.get_dtcm_usage_in_bytes(vertex_slice))

    def _get_sdram_usage_for_neuron_params(self, vertex_slice):
        """ Calculate the SDRAM usage for just the neuron parameters region.

        :param vertex_slice: the slice of atoms.
        :return: The SDRAM required for the neuron region
        """

        base = 0

        # We are currently not using the rate LUT, maybe remove
        if hasattr(self.__pynn_model, "_rate_based"):
            base = self.__neuron_impl.get_sdram_usage_for_rate_lut() + 1

        return (
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
            # 2 times for the in_partition array
            2 * (self.__neuron_impl.get_n_synapse_types() * 4) +
            # Incoming max partitions
            14 * 4 +
            self.__neuron_recorder.get_sdram_usage_in_bytes(vertex_slice) +
            self.__neuron_impl.get_sdram_usage_in_bytes(vertex_slice.n_atoms) +
            base)

    def _get_sdram_usage_for_atoms(
            self, vertex_slice, graph, machine_time_step):
        n_record = len(self.__neuron_impl.get_recordable_variables()) + 1
        sdram_requirement = (
            common_constants.SYSTEM_BYTES_REQUIREMENT +
            self._get_sdram_usage_for_neuron_params(vertex_slice) +
            recording_utilities.get_recording_header_size(n_record) +
            recording_utilities.get_recording_data_constant_size(n_record) +
            PopulationMachineVertex.get_provenance_data_size(
                PopulationMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            profile_utils.get_profile_region_size(
                self.__n_profile_samples))

        return sdram_requirement

    def _reserve_memory_regions(self, spec, vertex_slice, vertex):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=common_constants.SIMULATION_N_BYTES,
            label='System')

        self._reserve_neuron_params_data_region(spec, vertex_slice)

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.RECORDING.value,
            size=recording_utilities.get_recording_header_size(
                len(self.__neuron_impl.get_recordable_variables()) + 1))

        profile_utils.reserve_profile_region(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self.__n_profile_samples)

        vertex.reserve_provenance_data_region(spec)

    def _reserve_neuron_params_data_region(self, spec, vertex_slice):
        """ Reserve the neuron parameter data region.

        :param spec: the spec to write the DSG region to
        :param vertex_slice: the slice of atoms from the application vertex
        :return: None
        """
        params_size = self._get_sdram_usage_for_neuron_params(vertex_slice)
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=params_size,
            label='NeuronParams')

    # We PROBABLY DON'T NEED THE NEXT TWO METHODS ANYMORE!, KEPT FOR COMPATIBILITY NOW
    def _get_ring_buffer_to_input_left_shifts(
            self, application_vertex, application_graph, machine_timestep):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """
        weight_scale_squared = application_vertex.weight_scale * application_vertex.weight_scale
        n_synapse_types = application_vertex.implemented_synapse_types
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
                    if n_synapse_types > 1:
                        synapse_type = synapse_info.synapse_type
                    else:
                        synapse_type = 0
                    synapse_dynamics = synapse_info.synapse_dynamics
                    connector = synapse_info.connector
                    weight_mean = (
                        synapse_dynamics.get_weight_mean(connector, synapse_info.weight) *
                        application_vertex.weight_scale)
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
                        connector, synapse_info.weight) * application_vertex.weight_scale)
                    biggest_weight[synapse_type] = max(
                        biggest_weight[synapse_type], weight_max)

                    spikes_per_tick = max(
                        1.0, application_vertex.spikes_per_second / steps_per_second)
                    spikes_per_second = application_vertex.spikes_per_second
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
                        application_vertex.ring_buffer_sigma),
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

        return list(max_weight_powers)

    def _get_ring_buffer_shifts(
            self, application_graph, machine_timestep):
        """ Get the ring buffer shifts for this vertex
        """
        if self._ring_buffer_shifts is None:
            self._ring_buffer_shifts = [0 for _ in range(len(self.incoming_partitions))]
            previous_syn_type = -1
            for vertex in self._connected_app_vertices:
                if vertex.synapse_index != previous_syn_type:
                    # self._ring_buffer_shifts.extend(
                    #     self._get_ring_buffer_to_input_left_shifts(
                    #         vertex, application_graph,
                    #         machine_timestep))
                    self._ring_buffer_shifts[vertex.synapse_index] = vertex.ring_buffer_shifts[0]
                    previous_syn_type = vertex.synapse_index
        return self._ring_buffer_shifts
    
    @staticmethod
    def __copy_ranged_dict(source, merge=None, merge_keys=None):
        target = SpynnakerRangeDictionary(len(source))
        for key in source.keys():
            copy_list = SpynnakerRangedList(len(source))
            if merge_keys is None or key not in merge_keys:
                init_list = source.get_list(key)
            else:
                init_list = merge.get_list(key)
            for start, stop, value in init_list.iter_ranges():
                is_list = (hasattr(value, '__iter__') and
                           not isinstance(value, str))
                copy_list.set_value_by_slice(start, stop, value, is_list)
            target[key] = copy_list
        return target

    def _write_neuron_parameters(
            self, spec, key, vertex_slice, machine_time_step,
            time_scale_factor, application_graph, indices, mem_offset,
            index_offset):

        # If resetting, reset any state variables that need to be reset
        if (self.__has_reset_last and
                self.__initial_state_variables is not None):
            self._state_variables = self.__copy_ranged_dict(
                self.__initial_state_variables, self._state_variables,
                self.__updated_state_variables)
            self.__initial_state_variables = None

        # If no initial state variables, copy them now
        if self.__has_reset_last:
            self.__initial_state_variables = self.__copy_ranged_dict(
                self._state_variables)

        # Reset things that need resetting
        self.__has_reset_last = False
        self.__updated_state_variables.clear()

        # pylint: disable=too-many-arguments
        n_atoms = vertex_slice.n_atoms
        spec.comment("\nWriting Neuron Parameters for {} Neurons:\n".format(
            n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value)

        # Write the random back off value
        max_offset = (
            machine_time_step * time_scale_factor) // _MAX_OFFSET_DENOMINATOR
        spec.write_value(
            int(math.ceil(max_offset / self.__n_subvertices)) *
            self.__n_data_specs)
        self.__n_data_specs += 1

        # Write the number of microseconds between sending spikes
        time_between_spikes = (
            (machine_time_step * time_scale_factor) / (n_atoms * 100.0))
        spec.write_value(data=int(time_between_spikes))

        # Write whether the key is to be used, and then the key, or 0 if it
        # isn't to be used
        if key is None:
            spec.write_value(data=0)
            spec.write_value(data=0)
        else:
            spec.write_value(data=1)
            spec.write_value(data=key)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the number of synapse types
        spec.write_value(data=self.__neuron_impl.get_n_synapse_types())

        # Write the SDRAM offset for the input contributions
        spec.write_value(data=mem_offset)

        # Write the index offset in the partition to calculate which memory to read from first
        spec.write_value(data=index_offset)

        # Write the number of variables that can be recorded
        spec.write_value(
            data=len(self.__neuron_impl.get_recordable_variables()))

        # Write the number of incoming partitions per synapse type
        # to allocate a sufficiently big contribution area for all
        # the synapse cores.
        spec.write_array(self._incoming_partitions)

        # Write Synaptic contribution left shift
        ring_buffer_shifts = self._get_ring_buffer_shifts(
            application_graph, machine_time_step)

        spec.write_array(ring_buffer_shifts)

        spec.write_array(indices)

        # Write the recording data
        recording_data = self.__neuron_recorder.get_data(vertex_slice)
        spec.write_array(recording_data)

        # Remove offset from the slice to write correct neuron params
        new_slice = Slice(vertex_slice.lo_atom-self.atoms_offset,
                          vertex_slice.hi_atom-self.atoms_offset)

        # Write the neuron parameters
        neuron_data = self.__neuron_impl.get_data(
            self._parameters, self._state_variables, new_slice)
        spec.write_array(neuron_data)

        if hasattr(self.__pynn_model, "_rate_based"):
            rate_lut = self.__neuron_impl.generate_rate_lut()
            spec.write_value(data=len(rate_lut))
            spec.write_array(rate_lut)

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info):
        # pylint: disable=too-many-arguments, arguments-differ
        vertex_slice = graph_mapper.get_slice(placement.vertex)

        # reserve the neuron parameters data region
        self._reserve_neuron_params_data_region(
            spec, graph_mapper.get_slice(placement.vertex))

        # write the neuron params into the new DSG region
        self._write_neuron_parameters(
            key=routing_info.get_first_key_from_pre_vertex(
                placement.vertex, constants.SPIKE_PARTITION_ID),
            machine_time_step=machine_time_step, spec=spec,
            time_scale_factor=time_scale_factor,
            vertex_slice=vertex_slice,
            indices=placement.vertex.vertex_indices)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self.__change_requires_neuron_parameters_reload = False

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "application_graph": "MemoryApplicationGraph",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "application_graph", "machine_graph", "routing_info",
            "data_n_time_steps"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, application_graph, machine_graph, routing_info,
            data_n_time_steps):
        # pylint: disable=too-many-arguments, arguments-differ
        vertex = placement.vertex

        spec.comment("\n*** Spec for block of {} neurons ***\n".format(
            self.__neuron_impl.model_name))
        vertex_slice = graph_mapper.get_slice(vertex)

        # Reserve memory regions
        self._reserve_memory_regions(spec, vertex_slice, vertex)

        # Declare random number generators and distributions:
        # TODO add random distribution stuff
        # self.write_random_distribution_declarations(spec)

        # Get the key
        key = routing_info.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID)

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
            self._get_buffered_sdram(vertex_slice, data_n_time_steps)))


        for c in vertex.constraints:
            if isinstance(c, SameChipAsConstraint):# and isinstance(c.vertex, SynapseMachineVertex):
                vertex.index_at(c.vertex.mem_offset, c.vertex.vertex_index)

        
        # Write the neuron parameters
        self._write_neuron_parameters(
            spec, key, vertex_slice, machine_time_step,
            time_scale_factor, application_graph, vertex.vertex_indices,
            (self.__max_atoms_per_core*vertex.mem_offset), vertex.mem_offset)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self.__n_profile_samples)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):

        plastic = "_static"

        for vertex in self._connected_app_vertices:
            if vertex.has_plastic_synapses():
                plastic = "_plastic"

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(
            self.__neuron_impl.binary_name)

        # Reunite title and extension and return
        return (binary_title +
                plastic +
                binary_extension)

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__neuron_recorder.is_recording("spikes")

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        self.set_recording("spikes", new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self.__neuron_recorder.get_spikes(
            self.label, buffer_manager, self.SPIKE_RECORDING_REGION,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractNeuronRecordable.get_recordable_variables)
    def get_recordable_variables(self):
        return self.__neuron_recorder.get_recordable_variables()

    @overrides(AbstractNeuronRecordable.is_recording)
    def is_recording(self, variable):
        return self.__neuron_recorder.is_recording(variable)

    @overrides(AbstractNeuronRecordable.set_recording)
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        self.__change_requires_mapping = not self.is_recording(variable)
        self.__neuron_recorder.set_recording(
            variable, new_state, sampling_interval, indexes)

    @overrides(AbstractNeuronRecordable.get_data)
    def get_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        # pylint: disable=too-many-arguments
        index = 0
        if variable != "spikes":
            index = 1 + self.__neuron_impl.get_recordable_variable_index(
                variable)
        return self.__neuron_recorder.get_matrix_data(
            self.label, buffer_manager, index, placements, graph_mapper,
            self, variable, n_machine_time_steps)

    @overrides(AbstractNeuronRecordable.get_neuron_sampling_interval)
    def get_neuron_sampling_interval(self, variable):
        return self.__neuron_recorder.get_neuron_sampling_interval(variable)

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return self.__neuron_recorder.get_neuron_sampling_interval("spikes")

    @overrides(AbstractPopulationInitializable.initialize)
    def initialize(self, variable, value):
        if not self.__has_reset_last:
            raise Exception(
                "initialize can only be called before the first call to run, "
                "or before the first call to run after a reset")
        if variable not in self._state_variables:
            raise KeyError(
                "Vertex does not support initialisation of"
                " parameter {}".format(variable))
        self._state_variables.set_value(variable, value)
        self.__updated_state_variables.add(variable)
        self.__change_requires_neuron_parameters_reload = True

    @property
    def initialize_parameters(self):
        return self.__pynn_model.default_initial_values.keys()

    def _get_parameter(self, variable):
        if variable.endswith("_init"):
            # method called with "V_init"
            key = variable[:-5]
            if variable in self._state_variables:
                # variable is v and parameter is v_init
                return variable
            elif key in self._state_variables:
                # Oops neuron defines v and not v_init
                return key
        else:
            # method called with "v"
            if variable + "_init" in self._state_variables:
                # variable is v and parameter is v_init
                return variable + "_init"
            if variable in self._state_variables:
                # Oops neuron defines v and not v_init
                return variable

        # parameter not found for this variable
        raise KeyError("No variable {} found in {}".format(
            variable, self.__neuron_impl.model_name))

    @overrides(AbstractPopulationInitializable.get_initial_value)
    def get_initial_value(self, variable, selector=None):
        parameter = self._get_parameter(variable)

        ranged_list = self._state_variables[parameter]
        if selector is None:
            return ranged_list
        return ranged_list.get_values(selector)

    @overrides(AbstractPopulationInitializable.set_initial_value)
    def set_initial_value(self, variable, value, selector=None):
        parameter = self._get_parameter(variable)

        ranged_list = self._state_variables[parameter]
        ranged_list.set_value_by_selector(selector, value)

    @property
    def conductance_based(self):
        return self.__neuron_impl.is_conductance_based

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        """ Get a property of the overall model.
        """
        if key not in self._parameters:
            raise InvalidParameterType(
                "Population {} does not have parameter {}".format(
                    self.__neuron_impl.model_name, key))
        return self._parameters[key]

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        """ Set a property of the overall model.
        """
        if key not in self._parameters:
            raise InvalidParameterType(
                "Population {} does not have parameter {}".format(
                    self.__neuron_impl.model_name, key))
        self._parameters.set_value(key, value)
        self.__change_requires_neuron_parameters_reload = True

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address to where the neuron parameters are stored
        neuron_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
                transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        neuron_parameters_sdram_address = (
            neuron_region_sdram_address +
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS)

        # get size of neuron params
        size_of_region = self._get_sdram_usage_for_neuron_params(vertex_slice)
        size_of_region -= self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, neuron_parameters_sdram_address,
            size_of_region)

        # Skip the recorder globals as these are not change on machine
        # Just written out in case data is changed and written back
        offset = self.__neuron_recorder.get_sdram_usage_in_bytes(
            vertex_slice)

        # update python neuron parameters with the data
        self.__neuron_impl.read_data(
            byte_array, offset, vertex_slice, self._parameters,
            self._state_variables)

    @property
    def weight_scale(self):
        return self.__neuron_impl.get_global_weight_scale()

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        """ Gets the constraints for partitions going out of this vertex.

        :param partition: the partition that leaves this vertex
        :return: list of constraints
        """
        return [ContiguousKeyRangeContraint()]

    @overrides(
        AbstractNeuronRecordable.clear_recording)
    def clear_recording(
            self, variable, buffer_manager, placements, graph_mapper):
        index = 0
        if variable != "spikes":
            index = 1 + self.__neuron_impl.get_recordable_variable_index(
                variable)
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper, index)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper,
            AbstractPopulationVertex.SPIKE_RECORDING_REGION)

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

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        if self.__neuron_impl.is_recordable(variable):
            return self.__neuron_impl.get_recordable_units(variable)
        if variable not in self._parameters:
            raise Exception("Population {} does not have parameter {}".format(
                self.__neuron_impl.model_name, variable))
        return self.__neuron_impl.get_units(variable)

    def describe(self):
        """ Get a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context\
        will be returned.
        """
        parameters = dict()
        for parameter_name in self.__pynn_model.default_parameters:
            # BAD CODING : TMP FOR THE US NO TEACH!! FIX!!!!!!!!!!!!!!!!!!!!!
            if parameter_name != "teach" and parameter_name != "out":
                parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__neuron_impl.model_name,
            "default_parameters": self.__pynn_model.default_parameters,
            "default_initial_values": self.__pynn_model.default_parameters,
            "parameters": parameters,
        }
        return context

    def get_synapse_id_by_target(self, target):
        return self.__neuron_impl.get_synapse_id_by_target(target)

    #used to know how many synapse vertices we need
    def get_n_synapse_types(self):
        return self.__neuron_impl.get_n_synapse_types()

    def get_machine_vertex_at(self, low, high):

        vertices = list()

        for (lo, hi) in self._machine_vertices:
            if lo >= low and hi <= high:
                vertices.append(self._machine_vertices[(lo, hi)])

        return vertices

    def __str__(self):
        return "{} with {} atoms".format(self.label, self.n_atoms)

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractCanReset.reset_to_first_timestep)
    def reset_to_first_timestep(self):
        # Mark that reset has been done, and reload state variables
        self.__has_reset_last = True
        self.__change_requires_neuron_parameters_reload = True

        # If synapses change during the run,
        if self._connected_app_vertices[0].synapse_dynamics.changes_during_run:
            self.__change_requires_data_generation = True
            self.__change_requires_neuron_parameters_reload = False
