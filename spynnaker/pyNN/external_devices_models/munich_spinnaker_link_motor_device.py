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
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    FixedMaskConstraint)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex, ApplicationVertex)
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractVertexWithEdgeToDependentVertices)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES, BYTES_PER_WORD)
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults

logger = logging.getLogger(__name__)
MOTOR_PARTITION_ID = "MOTOR"


class _MunichMotorDevice(ApplicationSpiNNakerLinkVertex):
    __slots__ = []

    def __init__(self, spinnaker_link_id, board_address=None):
        super(_MunichMotorDevice, self).__init__(
            n_atoms=6, spinnaker_link_id=spinnaker_link_id,
            label="External Munich Motor", max_atoms_per_core=6,
            board_address=board_address)


@defaults
class MunichMotorDevice(
        ApplicationVertex, AbstractVertexWithEdgeToDependentVertices,
        AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
        AbstractProvidesOutgoingPartitionConstraints,
        ProvidesKeyToAtomMappingImpl):
    """ An Omnibot motor control device - has a real vertex and an external\
        device vertex
    """
    __slots__ = [
        "__continue_if_not_different",
        "__delay_time",
        "__delta_threshold",
        "__dependent_vertices",
        "__sample_time",
        "__speed",
        "__update_time"]

    SYSTEM_REGION = 0
    PARAMS_REGION = 1

    PARAMS_SIZE = 7 * BYTES_PER_WORD

    def __init__(
            self, spinnaker_link_id, board_address=None, speed=30,
            sample_time=4096, update_time=512, delay_time=5,
            delta_threshold=23, continue_if_not_different=True, label=None):
        # pylint: disable=too-many-arguments

        super(MunichMotorDevice, self).__init__(label)

        self.__speed = speed
        self.__sample_time = sample_time
        self.__update_time = update_time
        self.__delay_time = delay_time
        self.__delta_threshold = delta_threshold
        self.__continue_if_not_different = bool(continue_if_not_different)
        self.__dependent_vertices = [
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
            sdram=ConstantSDRAM(
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
        "routing_info": "MemoryRoutingInfos",
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "routing_info", "machine_time_step", "time_scale_factor"
        })
    def generate_data_specification(
            self, spec, placement, routing_info,
            machine_time_step, time_scale_factor):
        # pylint: disable=too-many-arguments, arguments-differ

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
        spec.write_value(data=self.__speed)
        spec.write_value(data=self.__sample_time)
        spec.write_value(data=self.__update_time)
        spec.write_value(data=self.__delay_time)
        spec.write_value(data=self.__delta_threshold)
        spec.write_value(data=int(self.__continue_if_not_different))

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "robot_motor_control.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def reserve_memory_regions(self, spec):
        """ Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            self.SYSTEM_REGION, SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            self.PARAMS_REGION, self.PARAMS_SIZE, label='params')

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        """ Return the vertices which this vertex depends upon
        """
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices.
               edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        """ Return the dependent edge identifier
        """
        return [MOTOR_PARTITION_ID]
