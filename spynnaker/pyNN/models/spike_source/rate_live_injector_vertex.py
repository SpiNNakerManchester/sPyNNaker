import logging
import math
import numpy
from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
    AbstractRewritesDataSpecification)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities import (
    helpful_functions, globals_variables)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet)
from .rate_source_live_machine_vertex import (
    RateSourceLiveMachineVertex)

# bool has_key; uint32_t key; uint32_t generators; uint32_t timer_offset; uint32_t refresh;
PARAMS_BASE_WORDS = 5

START_OF_RATE_GENERATOR_PARAMETERS = PARAMS_BASE_WORDS * 4

MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10

_REGIONS = RateSourceLiveMachineVertex.RATE_SOURCE_REGIONS

class RateLiveInjectorVertex(ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractChangableAfterRun, AbstractRewritesDataSpecification,
        ProvidesKeyToAtomMappingImpl):

    __slots__ = [
        "__model_name",
        "__model",
        "__connected_app_vertices",
        "__machine_vertex",
        "__change_requires_neuron_parameters_reload",
        "__self_machine_time_step",
        "__n_subvertices",
        "__n_data_specs",
        "__n_profile_samples",
        "__requires_mapping",
    ]

    _n_vertices = 0

    def __init__(self, label, constraints, model):
        # pylint: disable=too-many-arguments
        self.__model_name = "RateLiveInjector"
        self.__model = model

        self.__change_requires_neuron_parameters_reload = False
        self.__machine_time_step = None

        self.__n_subvertices = 0
        self.__n_data_specs = 0

        self.__connected_app_vertices = None
        self.__machine_vertex = None

        super(RateLiveInjectorVertex, self).__init__(
            label=label, constraints=constraints,
            max_atoms_per_core=1)

        # get config from simulator
        config = globals_variables.get_simulator().config
        self.__n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

        # used for reset and rerun
        self.__requires_mapping = True

    @property
    def connected_app_vertices(self):
        return self.__connected_app_vertices

    @connected_app_vertices.setter
    def connected_app_vertices(self, vertices):
        self.__connected_app_vertices = vertices

    @property
    def machine_vertex(self):
        return self.__machine_vertex
    
    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__requires_mapping = False

    @inject_items({
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={"machine_time_step"}
    )
    def get_resources_used_by_atoms(self, vertex_slice, machine_time_step):
        # pylint: disable=arguments-differ

        rate_params_sz = self.get_params_bytes(vertex_slice)
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            rate_params_sz +
            RateSourceLiveMachineVertex.get_provenance_data_size(
                RateSourceLiveMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            profile_utils.get_profile_region_size(self.__n_profile_samples))

        container = ResourceContainer(
            sdram=other,
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        return container

    def get_params_bytes(self, vertex_slice):
        """ Gets the size of the poisson parameters in bytes

        :param vertex_slice:
        """
        return PARAMS_BASE_WORDS * 4

    @property
    def n_atoms(self):
        return 1

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        # pylint: disable=too-many-arguments, arguments-differ

        self.__machine_vertex = RateSourceLiveMachineVertex(
            resources_required, False, constraints, label)

        RateLiveInjectorVertex._n_vertices += 1

        for app_vertex in self.__connected_app_vertices:
            for vertex in app_vertex.machine_vertices.values():
                self.__machine_vertex.add_constraint(SameChipAsConstraint(vertex))

        self.__n_subvertices += 1
        return self.__machine_vertex

    def reserve_memory_regions(self, spec, placement, graph_mapper):
        """ Reserve memory regions for rate source parameters and output\
            buffer.

        :param spec: the data specification writer
        :param placement: the location this vertex resides on in the machine
        :param graph_mapper: the mapping between app and machine graphs
        :return: None
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=_REGIONS.SYSTEM_REGION.value,
            size=SIMULATION_N_BYTES,
            label='setup')

        # reserve poisson params dsg region
        self._reserve_rate_params_region(placement, graph_mapper, spec)

        profile_utils.reserve_profile_region(
            spec, _REGIONS.PROFILER_REGION.value, self.__n_profile_samples)

        placement.vertex.reserve_provenance_data_region(spec)

    def _reserve_rate_params_region(self, placement, graph_mapper, spec):
        """ does the allocation for the rate params region itself, as\
            it can be reused for setters after an initial run

        :param placement: the location on machine for this vertex
        :param graph_mapper: the mapping between machine and application graphs
        :param spec: the dsg writer
        :return:  None
        """
        spec.reserve_memory_region(
            region=_REGIONS.RATE_PARAMS_REGION.value,
            size=self.get_params_bytes(graph_mapper.get_slice(
                placement.vertex)), label='RateParams')

    @staticmethod
    def get_dtcm_usage_for_atoms():
        return 0

    @staticmethod
    def get_cpu_usage_for_atoms():
        return 0

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "rate_live_injector.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def _write_rate_parameters(
            self, spec, graph, placement, routing_info,
            vertex_slice, machine_time_step, time_scale_factor,
            vertex_index):
        """ Generate Neuron Parameter data for rate sources

        :param spec: the data specification writer
        :param key: the routing key for this vertex
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        :param time_scale_factor:\
            the scaling between machine time step and real time
        :return: None
        """
        # pylint: disable=too-many-arguments, too-many-locals
        spec.comment("\nWriting Rate Parameters for {} rate sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(_REGIONS.RATE_PARAMS_REGION.value)

        # Write Key info for this core:
        key = routing_info.get_first_key_from_pre_vertex(
            placement.vertex, constants.SPIKE_PARTITION_ID)
        spec.write_value(data=1 if key is not None else 0)
        spec.write_value(data=key if key is not None else 0)

        # Write the number of generators
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the offset value
        max_offset = (
            machine_time_step * time_scale_factor) // _MAX_OFFSET_DENOMINATOR
        spec.write_value(
            int(math.ceil(max_offset / self.__n_subvertices)) *
            self.__n_data_specs)
        self.__n_data_specs += 1

        # Write the refesh rate
        spec.write_value(data=self.__refresh_rate)


    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "graph": "MemoryMachineGraph"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "graph"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, graph):
        # pylint: disable=too-many-arguments, arguments-differ

        # reserve the neuron parameters data region
        self._reserve_rate_params_region(placement, graph_mapper, spec)

        # allocate parameters
        self._write_rate_parameters(
            spec=spec, graph=graph, placement=placement,
            routing_info=routing_info,
            vertex_slice=graph_mapper.get_slice(placement.vertex),
            machine_time_step=machine_time_step,
            time_scale_factor=time_scale_factor)

        # end spec
        spec.end_specification()

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "graph": "MemoryMachineGraph"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "data_n_time_steps", "graph"
        }
    )
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, data_n_time_steps, graph):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__machine_time_step = machine_time_step
        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        spec.comment("\n*** Spec for RateSource Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(spec, placement, graph_mapper)

        # write setup data
        spec.switch_write_focus(_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        vertex.vertex_index = placement.p

        for c in vertex.constraints:
            if isinstance(c, SameChipAsConstraint):
                c.vertex.vertex_index = placement.p

        # write parameters
        self._write_rate_parameters(
            spec, graph, placement, routing_info, vertex_slice,
            machine_time_step, time_scale_factor, vertex.vertex_index)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, _REGIONS.PROFILER_REGION.value,
            self.__n_profile_samples)

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self.__change_requires_neuron_parameters_reload = False

    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self.__change_requires_neuron_parameters_reload

    def describe(self):
        """ Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template\
        context will be returned.
        """

        parameters = dict()
        for parameter_name in self.__model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context
