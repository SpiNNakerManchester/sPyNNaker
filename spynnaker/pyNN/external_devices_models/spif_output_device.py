# Copyright (c) 2022 The University of Manchester
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
from pacman.model.graphs.application.application_2d_fpga_vertex import Application2DFPGAVertex
from spinn_front_end_common.abstract_models.abstract_send_me_multicast_commands_vertex import AbstractSendMeMulticastCommandsVertex

class SPIFOutputDevice(Application2DFPGAVertex, AbstractSendMeMulticastCommandsVertex):