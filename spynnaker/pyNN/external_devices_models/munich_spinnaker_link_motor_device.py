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
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex)
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from spinn_front_end_common.abstract_models import (
    AbstractVertexWithEdgeToDependentVertices)
from spynnaker.pyNN.models.defaults import defaults
from .machine_munich_motor_device import MachineMunichMotorDevice


class _MunichMotorDevice(ApplicationSpiNNakerLinkVertex):
    __slots__ = []

    def __init__(self, spinnaker_link_id, board_address=None):
        super().__init__(
            n_atoms=6, spinnaker_link_id=spinnaker_link_id,
            label="External Munich Motor", board_address=board_address)


@defaults
class MunichMotorDevice(
        AbstractOneAppOneMachineVertex,
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
        :param board_address:
        :type board_address: str or None
        :param int speed:
        :param int sample_time:
        :param int update_time:
        :param int delay_time:
        :param int delta_threshold:
        :param bool continue_if_not_different:
        :param str label:
        :type label: str or None
        """
        # pylint: disable=too-many-arguments

        m_vertex = MachineMunichMotorDevice(
            speed, sample_time, update_time, delay_time, delta_threshold,
            continue_if_not_different, label, app_vertex=self)
        super().__init__(
            m_vertex, label, None, MachineMunichMotorDevice._N_ATOMS)
        self.__dependent_vertices = [
            _MunichMotorDevice(spinnaker_link_id, board_address)]

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices.
               edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(self, vertex):
        yield self.machine_vertex.MOTOR_PARTITION_ID
