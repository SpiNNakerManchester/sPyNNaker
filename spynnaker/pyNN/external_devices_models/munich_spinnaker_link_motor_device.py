# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Iterable, Optional
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from spinn_front_end_common.abstract_models import (
    AbstractVertexWithEdgeToDependentVertices)
from spynnaker.pyNN.models.defaults import AbstractProvidesDefaults
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from .machine_munich_motor_device import MachineMunichMotorDevice


class _MunichMotorDevice(ApplicationSpiNNakerLinkVertex):
    __slots__ = ()

    def __init__(self, spinnaker_link_id: int,
                 board_address: Optional[str] = None):
        super().__init__(
            n_atoms=6, spinnaker_link_id=spinnaker_link_id,
            label="External Munich Motor", board_address=board_address)


class MunichMotorDevice(
        AbstractOneAppOneMachineVertex,
        AbstractVertexWithEdgeToDependentVertices,
        PopulationApplicationVertex,
        AbstractProvidesDefaults):
    """
    An Omnibot motor control device. This has a real vertex and an
    external device vertex.
    """

    __slots__ = ("__dependent_vertices", )

    def __init__(
            self, spinnaker_link_id: int, board_address: Optional[str] = None,
            speed: int = 30, sample_time: int = 4096, update_time: int = 512,
            delay_time: int = 5, delta_threshold: int = 23,
            continue_if_not_different: bool = True,
            label: Optional[str] = None):
        """
        :param spinnaker_link_id:
            The SpiNNaker link to which the motor is connected
        :param board_address:
        :param speed:
        :param sample_time:
        :param update_time:
        :param delay_time:
        :param delta_threshold:
        :param continue_if_not_different:
        :param label:
        """
        m_vertex = MachineMunichMotorDevice(
            speed, sample_time, update_time, delay_time, delta_threshold,
            continue_if_not_different, label, app_vertex=self)
        super().__init__(
            m_vertex, label, MachineMunichMotorDevice._N_ATOMS)
        self.__dependent_vertices = [
            _MunichMotorDevice(spinnaker_link_id, board_address)]

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self) -> Iterable[ApplicationVertex]:
        return self.__dependent_vertices

    @overrides(AbstractVertexWithEdgeToDependentVertices.
               edge_partition_identifiers_for_dependent_vertex)
    def edge_partition_identifiers_for_dependent_vertex(
            self, vertex: ApplicationVertex) -> Iterable[str]:
        yield self.machine_vertex.MOTOR_PARTITION_ID
