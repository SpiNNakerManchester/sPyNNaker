# spynnaker imports
import logging

from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints \
    import FixedMaskConstraint
from pacman.model.decorators import overrides
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.graphs.application \
    import ApplicationSpiNNakerLinkVertex, ApplicationVertex
from pacman.model.resources import CPUCyclesPerTickResource, DTCMResource
from pacman.model.resources import ResourceContainer, SDRAMResource
from spinn_front_end_common.abstract_models import\
    AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary
from spinn_front_end_common.abstract_models\
    import AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models.impl import \
    ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.abstract_models \
    import AbstractVertexWithEdgeToDependentVertices
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import SYSTEM_BYTES_REQUIREMENT
from spynnaker.pyNN.exceptions import SpynnakerException

logger = logging.getLogger(__name__)

MOTOR_PARTITION_ID = "MOTOR"


class _MunichMotorDevice(ApplicationSpiNNakerLinkVertex):

    def __init__(self, spinnaker_link_id, board_address=None):

        ApplicationSpiNNakerLinkVertex.__init__(
            self, n_atoms=6, spinnaker_link_id=spinnaker_link_id,
            label="External Munich Motor", max_atoms_per_core=6,
            board_address=board_address)


class MunichMotorDevice(
        AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
        ApplicationVertex, AbstractVertexWithEdgeToDependentVertices,
        AbstractProvidesOutgoingPartitionConstraints,
        ProvidesKeyToAtomMappingImpl):
    """ An Omnibot motor control device - has a real vertex and an external\
        device vertex
    """

    SYSTEM_REGION = 0
    PARAMS_REGION = 1

    PARAMS_SIZE = 7 * 4

    default_parameters = {
        'speed': 30, 'sample_time': 4096, 'update_time': 512, 'delay_time': 5,
        'delta_threshold': 23, 'continue_if_not_different': True,
        'label': "RobotMotorControl", 'board_address': None}

    def __init__(
            self, n_neurons, spinnaker_link_id,
            board_address=default_parameters['board_address'],
            speed=default_parameters['speed'],
            sample_time=default_parameters['sample_time'],
            update_time=default_parameters['update_time'],
            delay_time=default_parameters['delay_time'],
            delta_threshold=default_parameters['delta_threshold'],
            continue_if_not_different=default_parameters[
                'continue_if_not_different'],
            label=default_parameters['label']):
        """
        """

        if n_neurons != 6:
            logger.warning(
                "The specified number of neurons for the munich motor"
                " device has been ignored; 6 will be used instead")

        ApplicationVertex.__init__(self, label)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        ProvidesKeyToAtomMappingImpl.__init__(self)

        self._speed = speed
        self._sample_time = sample_time
        self._update_time = update_time
        self._delay_time = delay_time
        self._delta_threshold = delta_threshold
        self._continue_if_not_different = continue_if_not_different
        self._dependent_vertices = [
            _MunichMotorDevice(spinnaker_link_id, board_address)]

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return 6

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(self, vertex_slice, resources_required,
                              label=None, constraints=None):
        return SimpleMachineVertex(
            resources_required, label, constraints)

    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer(
            sdram=SDRAMResource(
                SYSTEM_BYTES_REQUIREMENT + self.PARAMS_SIZE),
            dtcm=DTCMResource(0), cpu_cycles=CPUCyclesPerTickResource(0))

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):

        # Any key to the device will work, as long as it doesn't set the
        # management bit.  We also need enough for the configuration bits
        # and the management bit anyway
        return list([FixedMaskConstraint(0xFFFFF800)])

    @inject_items({
        "graph_mapper": "MemoryGraphMapper",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "application_graph": "MemoryApplicationGraph",
        "tags": "MemoryTags",
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "graph_mapper", "application_graph", "machine_graph",
            "routing_info", "tags", "machine_time_step",
            "time_scale_factor"
        })
    def generate_data_specification(
            self, spec, placement, graph_mapper, application_graph,
            machine_graph, routing_info, tags,
            machine_time_step, time_scale_factor):
        iptags = tags.get_ip_tags_for_vertex(placement.vertex)
        reverse_iptags = tags.get_reverse_ip_tags_for_vertex(placement.vertex)
        self.generate_application_data_specification(
            spec, placement, graph_mapper, application_graph, machine_graph,
            routing_info, iptags, reverse_iptags, machine_time_step,
            time_scale_factor)

    def generate_application_data_specification(
            self, spec, placement, graph_mapper, application_graph,
            machine_graph, routing_info, iptags, reverse_iptags,
            machine_time_step, time_scale_factor):

        # reserve regions
        self.reserve_memory_regions(spec)

        # Write the setup region
        spec.comment("\n*** Spec for robot motor control ***\n\n")

        # handle simulation data
        spec.switch_write_focus(self.SYSTEM_REGION)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # Get the key
        edge_key = routing_info.get_first_key_from_pre_vertex(
            placement.vertex, MOTOR_PARTITION_ID)
        if edge_key is None:
            raise SpynnakerException(
                "This motor should have one outgoing edge to the robot")

        # write params to memory
        spec.switch_write_focus(region=self.PARAMS_REGION)
        spec.write_value(data=edge_key)
        spec.write_value(data=self._speed)
        spec.write_value(data=self._sample_time)
        spec.write_value(data=self._update_time)
        spec.write_value(data=self._delay_time)
        spec.write_value(data=self._delta_threshold)
        if self._continue_if_not_different:
            spec.write_value(data=1)
        else:
            spec.write_value(data=0)

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "robot_motor_control.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def reserve_memory_regions(self, spec):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=self.SYSTEM_REGION,
            size=SYSTEM_BYTES_REQUIREMENT,
            label='setup')

        spec.reserve_memory_region(region=self.PARAMS_REGION,
                                   size=self.PARAMS_SIZE,
                                   label='params')

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        """ Return the vertices which this vertex depends upon
        """
        return self._dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices.
               edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        """ Return the dependent edge identifier
        """
        return [MOTOR_PARTITION_ID]
