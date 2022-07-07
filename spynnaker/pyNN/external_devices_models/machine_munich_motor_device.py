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

from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary)
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl, ProvenanceWriter)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES, BYTES_PER_WORD)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spynnaker.pyNN.exceptions import SpynnakerException


class MachineMunichMotorDevice(
        MachineVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary,
        ProvidesProvenanceDataFromMachineImpl):
    """ An Omnibot motor control device. This has a real vertex and an \
        external device vertex.
    """
    __slots__ = [
        "__continue_if_not_different",
        "__delay_time",
        "__delta_threshold",
        "__sample_time",
        "__speed",
        "__update_time"]

    MOTOR_PARTITION_ID = "MOTOR"

    # By asking for this number of keys, we will get a mask of 0xFFFFF800,
    # which works with the motor control protocol correctly
    _MOTOR_N_KEYS = 2048

    _N_ATOMS = 6

    _SYSTEM_REGION = 0
    _PARAMS_REGION = 1
    _PROVENANCE_REGION = 2

    _PROVENANCE_ELEMENTS = 1

    _PARAMS_SIZE = 7 * BYTES_PER_WORD

    #: The name of the provenance item saying that packets were lost.
    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"

    def __init__(
            self, speed, sample_time, update_time, delay_time,
            delta_threshold, continue_if_not_different,
            label=None, constraints=None, app_vertex=None):
        """
        :param int speed:
        :param int sample_time:
        :param int update_time:
        :param int delay_time:
        :param int delta_threshold:
        :param bool continue_if_not_different:
        :param str label:
        :param constraints:
        :param app_vertex:
        """
        super().__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=Slice(0, self._N_ATOMS - 1))
        self.__speed = speed
        self.__sample_time = sample_time
        self.__update_time = update_time
        self.__delay_time = delay_time
        self.__delta_threshold = delta_threshold
        self.__continue_if_not_different = bool(continue_if_not_different)

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return ResourceContainer(
            sdram=ConstantSDRAM(
                SYSTEM_BYTES_REQUIREMENT + self._PARAMS_SIZE +
                self.get_provenance_data_size(self._PROVENANCE_ELEMENTS)),
            dtcm=DTCMResource(0), cpu_cycles=CPUCyclesPerTickResource(0))

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "robot_motor_control.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self._PROVENANCE_REGION

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return self._PROVENANCE_ELEMENTS

    @overrides(
        ProvidesProvenanceDataFromMachineImpl.parse_extra_provenance_items)
    def parse_extra_provenance_items(
            self, label, x, y, p, provenance_data):
        n_buffer_overflows, = provenance_data

        with ProvenanceWriter() as db:
            db.insert_core(x, y, p, self.INPUT_BUFFER_FULL_NAME,
                           n_buffer_overflows)
            if n_buffer_overflows > 0:
                db.insert_report(
                    f"The input buffer for {label} lost packets on "
                    f"{n_buffer_overflows} occasions. "
                    "This is often a sign that the system is running too "
                    "quickly for the number of neurons per core.  "
                    "Please increase the timer_tic or time_scale_factor "
                    "or decrease the number of neurons per core.")

    @inject_items({"routing_info": "RoutingInfos"})
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={"routing_info"})
    def generate_data_specification(self, spec, placement, routing_info):
        # pylint: disable=too-many-arguments, arguments-differ

        # reserve regions
        self.reserve_memory_regions(spec)

        # Write the setup region
        spec.comment("\n*** Spec for robot motor control ***\n\n")

        # handle simulation data
        spec.switch_write_focus(self._SYSTEM_REGION)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            placement.vertex.get_binary_file_name()))

        # Get the key
        edge_key = routing_info.get_first_key_from_pre_vertex(
            placement.vertex, self.MOTOR_PARTITION_ID)
        if edge_key is None:
            raise SpynnakerException(
                "This motor should have one outgoing edge to the robot")

        # write params to memory
        spec.switch_write_focus(region=self._PARAMS_REGION)
        spec.write_value(data=edge_key)
        spec.write_value(data=self.__speed)
        spec.write_value(data=self.__sample_time)
        spec.write_value(data=self.__update_time)
        spec.write_value(data=self.__delay_time)
        spec.write_value(data=self.__delta_threshold)
        spec.write_value(data=int(self.__continue_if_not_different))

        # End-of-Spec:
        spec.end_specification()

    def reserve_memory_regions(self, spec):
        """ Reserve SDRAM space for memory areas:

        #. Area for information on what data to record
        #. area for start commands
        #. area for end commands

        :param spec: The data specification to write to
        :type spec: ~data_specification.DataSpecificationGenerator
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            self._SYSTEM_REGION, SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            self._PARAMS_REGION, self._PARAMS_SIZE, label='params')

        self.reserve_provenance_data_region(spec)

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id):
        if partition_id == self.MOTOR_PARTITION_ID:
            return self._MOTOR_N_KEYS
        return super(MachineMunichMotorDevice, self).get_n_keys_for_partition(
            partition_id)
