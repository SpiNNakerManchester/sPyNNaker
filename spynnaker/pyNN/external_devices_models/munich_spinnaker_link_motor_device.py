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
from pacman.model.constraints.key_allocator_constraints import (
    FixedMaskConstraint)
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex)
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractVertexWithEdgeToDependentVertices)
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from spynnaker.pyNN.models.defaults import defaults
from .machine_munich_motor_device import MachineMunichMotorDevice

logger = logging.getLogger(__name__)


class _MunichMotorDevice(ApplicationSpiNNakerLinkVertex):
    __slots__ = []

    def __init__(self, spinnaker_link_id, board_address=None):
        super(_MunichMotorDevice, self).__init__(
            n_atoms=6, spinnaker_link_id=spinnaker_link_id,
            label="External Munich Motor", max_atoms_per_core=6,
            board_address=board_address)


@defaults
class MunichMotorDevice(
        AbstractOneAppOneMachineVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractVertexWithEdgeToDependentVertices):
    """ An Omnibot motor control device. This has a real vertex and an \
        external device vertex.
    """

    __slots__ = ["__dependent_vertices"]

    def __init__(
            self, spinnaker_link_id, board_address=None, speed=30,
            sample_time=4096, update_time=512, delay_time=5,
            delta_threshold=23, continue_if_not_different=True, label=None):
        """
        :param int spinnaker_link_id:
            The SpiNNaker link to which the motor is connected
        :param str board_address:
        :param int speed:
        :param int sample_time:
        :param int update_time:
        :param int delay_time:
        :param int delta_threshold:
        :param bool continue_if_not_different:
        :param str label:
        """
        # pylint: disable=too-many-arguments

        m_vertex = MachineMunichMotorDevice(
            speed, sample_time, update_time, delay_time, delta_threshold,
            continue_if_not_different, label, app_vertex=self)
        super(MunichMotorDevice, self).__init__(
            m_vertex, label, None, m_vertex.N_ATOMS)
        self.__dependent_vertices = [
            _MunichMotorDevice(spinnaker_link_id, board_address)]

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
        return [self.machine_vertex.MOTOR_PARTITION_ID]

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):

        # Any key to the device will work, as long as it doesn't set the
        # management bit.  We also need enough for the configuration bits
        # and the management bit anyway
        return list([FixedMaskConstraint(0xFFFFF800)])
