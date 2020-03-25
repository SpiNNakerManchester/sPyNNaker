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
from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractProvidesIncomingPartitionConstraints,
    AbstractProvidesOutgoingPartitionConstraints, AbstractHasAssociatedBinary,
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification,
    AbstractCanReset)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.utilities import (
    constants as common_constants, helpful_functions, globals_variables)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.simulation import simulation_utilities
from spynnaker.pyNN.utilities.constants import POPULATION_BASED_REGIONS
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable, NeuronRecorder)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractAcceptsIncomingSynapses,
    AbstractPopulationSettable, AbstractReadParametersBeforeSet,
    AbstractContainsUnits)
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.ranged import (
    SpynnakerRangeDictionary, SpynnakerRangedList)
from .synaptic_manager import SynapticManager
from .population_machine_vertex import PopulationMachineVertex

logger = logging.getLogger(__name__)

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 9 * BYTES_PER_WORD
_NEURON_BASE_SDRAM_USAGE_IN_BYTES = 3 * BYTES_PER_WORD
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

# TODO: Make sure these values are correct (particularly CPU cycles)
_C_MAIN_BASE_DTCM_USAGE_IN_BYTES = 3 * BYTES_PER_WORD
_C_MAIN_BASE_SDRAM_USAGE_IN_BYTES = 18 * BYTES_PER_WORD
_C_MAIN_BASE_N_CPU_CYCLES = 0

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10


class AbstractPopulationVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractContainsUnits,
        AbstractSpikeRecordable,  AbstractNeuronRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesIncomingPartitionConstraints,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractChangableAfterRun,
        AbstractRewritesDataSpecification, AbstractReadParametersBeforeSet,
        AbstractAcceptsIncomingSynapses, ProvidesKeyToAtomMappingImpl,
        AbstractCanReset):
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
        "__n_subvertices",
        "__n_data_specs",
        "__initial_state_variables",
        "__has_reset_last",
        "__updated_state_variables"]

    BASIC_MALLOC_USAGE = 2

    # the size of the runtime SDP port data region
    RUNTIME_SDP_PORT_SIZE = BYTES_PER_WORD

    # 7 elements before the start of global parameters
    # 1. random back off, 2. micro secs before spike, 3. has key, 4. key,
    # 5. n atoms, 6. n synapse types, 7. incoming spike buffer size.
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 7 * BYTES_PER_WORD

    _n_vertices = 0

    def __init__(
            self, n_neurons, label, constraints, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            neuron_impl, pynn_model):
        # pylint: disable=too-many-arguments, too-many-locals
        super(AbstractPopulationVertex, self).__init__(
            label, constraints, max_atoms_per_core)

        self.__n_atoms = n_neurons
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # buffer data
        self.__incoming_spike_buffer_size = incoming_spike_buffer_size

        # get config from simulator
        config = globals_variables.get_simulator().config

        if incoming_spike_buffer_size is None:
            self.__incoming_spike_buffer_size = config.getint(
                "Simulation", "incoming_spike_buffer_size")

        self.__neuron_impl = neuron_impl
        self.__pynn_model = pynn_model
        self._parameters = SpynnakerRangeDictionary(n_neurons)
        self._state_variables = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_parameters(self._parameters)
        self.__neuron_impl.add_state_variables(self._state_variables)
        self.__initial_state_variables = None
        self.__updated_state_variables = set()

        # Set up for recording
        recordable_variables = list(
            self.__neuron_impl.get_recordable_variables())
        record_data_types = dict(
            self.__neuron_impl.get_recordable_data_types())
        self.__neuron_recorder = NeuronRecorder(
            recordable_variables, record_data_types, [NeuronRecorder.SPIKES],
            n_neurons)

        # Set up synapse handling
        self.__synapse_manager = SynapticManager(
            self.__neuron_impl.get_n_synapse_types(), ring_buffer_sigma,
            spikes_per_second, config)

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
    @overrides(AbstractChangableAfterRun.requires_data_generation)
    def requires_data_generation(self):
        return self.__change_requires_data_generation

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False
        self.__change_requires_data_generation = False

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):

        self.__n_subvertices += 1
        recorded_region_ids = self.__neuron_recorder.recorded_ids_by_slice(
            vertex_slice)
        return PopulationMachineVertex(
            resources_required, recorded_region_ids,
            label, constraints)

    def get_cpu_usage_for_atoms(self, vertex_slice):
        return (
            _NEURON_BASE_N_CPU_CYCLES + _C_MAIN_BASE_N_CPU_CYCLES +
            (_NEURON_BASE_N_CPU_CYCLES_PER_NEURON * vertex_slice.n_atoms) +
            self.__neuron_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
            self.__neuron_impl.get_n_cpu_cycles(vertex_slice.n_atoms) +
            self.__synapse_manager.get_n_cpu_cycles())

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        return (
            _NEURON_BASE_DTCM_USAGE_IN_BYTES +
            self.__neuron_impl.get_dtcm_usage_in_bytes(vertex_slice.n_atoms) +
            self.__neuron_recorder.get_dtcm_usage_in_bytes(vertex_slice) +
            self.__synapse_manager.get_dtcm_usage_in_bytes())

    def _get_sdram_usage_for_neuron_params(self, vertex_slice):
        """ Calculate the SDRAM usage for just the neuron parameters region.

        :param vertex_slice: the slice of atoms.
        :return: The SDRAM required for the neuron region
        """
        return (
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
            self.__neuron_impl.get_sdram_usage_in_bytes(vertex_slice.n_atoms))

    def _get_sdram_usage_for_atoms(
            self, vertex_slice, graph, machine_time_step):
        sdram_requirement = (
            SYSTEM_BYTES_REQUIREMENT +
            self._get_sdram_usage_for_neuron_params(vertex_slice) +
            self._neuron_recorder.get_static_sdram_usage(vertex_slice) +
            PopulationMachineVertex.get_provenance_data_size(
                PopulationMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            self.__synapse_manager.get_sdram_usage_in_bytes(
                vertex_slice, machine_time_step, graph, self) +
            profile_utils.get_profile_region_size(self.__n_profile_samples))

        return sdram_requirement

    def _reserve_memory_regions(self, spec, vertex_slice, vertex):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYSTEM.value,
            size=common_constants.SIMULATION_N_BYTES,
            label='System')

        self._reserve_neuron_params_data_region(spec, vertex_slice)

        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.NEURON_RECORDING.value,
            size=self._neuron_recorder.get_static_sdram_usage(vertex_slice),
            label="neuron recording")

        profile_utils.reserve_profile_region(
            spec, POPULATION_BASED_REGIONS.PROFILING.value,
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
            region=POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=params_size, label='NeuronParams')

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
            time_scale_factor):

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
            (machine_time_step * time_scale_factor) / (n_atoms * 2.0))
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

        # Write the size of the incoming spike buffer
        spec.write_value(data=self.__incoming_spike_buffer_size)

        # Write the neuron parameters
        neuron_data = self.__neuron_impl.get_data(
            self._parameters, self._state_variables, vertex_slice)
        spec.write_array(neuron_data)

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
            vertex_slice=vertex_slice)

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

        # Write the neuron recording region
        self._neuron_recorder.write_neuron_recording_region(
            spec, POPULATION_BASED_REGIONS.NEURON_RECORDING.value,
            vertex_slice, data_n_time_steps)

        # Write the neuron parameters
        self._write_neuron_parameters(
            spec, key, vertex_slice, machine_time_step, time_scale_factor)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self.__n_profile_samples)

        # Get the weight_scale value from the appropriate location
        weight_scale = self.__neuron_impl.get_global_weight_scale()

        # allow the synaptic matrix to write its data spec-able data
        self.__synapse_manager.write_data_spec(
            spec, self, vertex_slice, vertex, placement, machine_graph,
            application_graph, routing_info, graph_mapper,
            weight_scale, machine_time_step)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(
            self.__neuron_impl.binary_name)

        # Reunite title and extension and return
        return (binary_title +
                self.__synapse_manager.vertex_executable_suffix +
                binary_extension)

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__neuron_recorder.is_recording(NeuronRecorder.SPIKES)

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        self.set_recording(
            NeuronRecorder.SPIKES, new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self.__neuron_recorder.get_spikes(
            self.label, buffer_manager,
            len(self.__neuron_impl.get_recordable_variables()),
            placements, graph_mapper, self, NeuronRecorder.SPIKES,
            machine_time_step)

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
        return self.__neuron_recorder.get_matrix_data(
            self.label, buffer_manager,
            self.__neuron_impl.get_recordable_variable_index(variable),
            placements, graph_mapper, self, variable, n_machine_time_steps)

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
        if variable not in self._state_variables:
            raise KeyError(
                "Vertex does not support initialisation of"
                " parameter {}".format(variable))

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
                placement, POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
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

        # update python neuron parameters with the data
        self.__neuron_impl.read_data(
            byte_array, 0, vertex_slice, self._parameters,
            self._state_variables)

    @property
    def weight_scale(self):
        return self.__neuron_impl.get_global_weight_scale()

    @property
    def ring_buffer_sigma(self):
        return self.__synapse_manager.ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__synapse_manager.ring_buffer_sigma = ring_buffer_sigma

    def reset_ring_buffer_shifts(self):
        self.__synapse_manager.reset_ring_buffer_shifts()

    @property
    def spikes_per_second(self):
        return self.__synapse_manager.spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__synapse_manager.spikes_per_second = spikes_per_second

    @property
    def synapse_dynamics(self):
        return self.__synapse_manager.synapse_dynamics

    def set_synapse_dynamics(self, synapse_dynamics):
        self.__synapse_manager.synapse_dynamics = synapse_dynamics

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        # pylint: disable=arguments-differ
        self.__synapse_manager.add_pre_run_connection_holder(
            connection_holder, edge, synapse_info)

    def get_connection_holders(self):
        return self.__synapse_manager.get_connection_holders()

    @overrides(AbstractAcceptsIncomingSynapses.get_connections_from_machine)
    def get_connections_from_machine(
            self, transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements=None, monitor_api=None, monitor_cores=None,
            handle_time_out_configuration=True, fixed_routes=None,
            extra_monitor=None):
        # pylint: disable=too-many-arguments
        return self.__synapse_manager.get_connections_from_machine(
            transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements, monitor_api, monitor_cores,
            handle_time_out_configuration, fixed_routes, extra_monitor)

    def clear_connection_cache(self):
        self.__synapse_manager.clear_connection_cache()

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self.__synapse_manager.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @overrides(AbstractProvidesIncomingPartitionConstraints.
               get_incoming_partition_constraints)
    def get_incoming_partition_constraints(self, partition):
        """ Gets the constraints for partitions going into this vertex.

        :param partition: partition that goes into this vertex
        :return: list of constraints
        """
        return self.__synapse_manager.get_incoming_partition_constraints()

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
        if variable == NeuronRecorder.SPIKES:
            index = len(self.__neuron_impl.get_recordable_variables())
        else:
            index = (
                self.__neuron_impl.get_recordable_variable_index(variable))
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper, index)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper,
            len(self.__neuron_impl.get_recordable_variables()))

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
        if variable == NeuronRecorder.SPIKES:
            return NeuronRecorder.SPIKES
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

    def __str__(self):
        return "{} with {} atoms".format(self.label, self.n_atoms)

    def __repr__(self):
        return self.__str__()

    def gen_on_machine(self, vertex_slice):
        return self.__synapse_manager.gen_on_machine(vertex_slice)

    @overrides(AbstractCanReset.reset_to_first_timestep)
    def reset_to_first_timestep(self):
        # Mark that reset has been done, and reload state variables
        self.__has_reset_last = True
        self.__change_requires_neuron_parameters_reload = True

        # If synapses change during the run,
        if self.__synapse_manager.changes_during_run:
            self.__change_requires_data_generation = True
            self.__change_requires_neuron_parameters_reload = False
