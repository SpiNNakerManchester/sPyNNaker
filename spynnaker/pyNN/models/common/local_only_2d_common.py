# Copyright (c) 2023 The University of Manchester
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
from math import ceil, log2, floor
from collections import namedtuple, defaultdict
from pacman.model.graphs.application import ApplicationVirtualVertex
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.common.mdslice import MDSlice
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.utilities.utility_calls import get_n_bits

#: The number of bits in a short value
BITS_PER_SHORT = 16

#: The number of bits in a byte value
BITS_PER_BYTE = 8

#: The number of bits to represent n_colour_bits
N_COLOUR_BITS_BITS = 3

#: Key info size in bytes
KEY_INFO_SIZE = 4 * BYTES_PER_WORD

#: A source
Source = namedtuple(
    "Source", ["projection", "local_delay", "delay_stage"])


def get_div_const(value):
    """ Get the values used to perform fast division by an integer constant

    :param int value: The value to be divided by
    :return: The values required encoded as fields of a 32-bit integer
    :rtype: int
    """
    log_val = int(ceil(log2(value)))
    log_m_val = ((2 ** log_val) - value) / value
    m = int(floor((2 ** BITS_PER_SHORT) * log_m_val) + 1)
    sh1 = min(log_val, 1)
    sh2 = max(log_val - 1, 0)
    return ((sh2 << (BITS_PER_SHORT + BITS_PER_BYTE))
            + (sh1 << BITS_PER_SHORT) + m)


def get_delay_for_source(incoming):
    """ Get the vertex which will send data from a given source projection,
        along with the delay stage and locally-handled delay valule

    :param Projection incoming: The incoming projection to get the delay from
    :return: The vertex, the local delay, the delay stage
    :rtype: ApplicationVertex, int, int
    """
    # pylint: disable=protected-access
    app_edge = incoming._projection_edge
    delay = incoming._synapse_information.synapse_dynamics.delay
    steps = delay * SpynnakerDataView.get_simulation_time_step_per_ms()
    max_delay = app_edge.post_vertex.splitter.max_support_delay()
    local_delay = steps % max_delay
    delay_stage = 0
    pre_vertex = app_edge.pre_vertex
    if steps > max_delay:
        delay_stage = (steps // max_delay) - 1
        pre_vertex = app_edge.delay_edge.pre_vertex
    return pre_vertex, local_delay, delay_stage


def get_rinfo_for_source(pre_vertex):
    """
    Get the routing information for the source of a projection.

    :param ApplicationVertex pre_vertex: The source of incoming data
    :return: Routing information, core mask, core mask shift
    :rtype: AppVertexRoutingInfo, int, int
    """
    routing_info = SpynnakerDataView.get_routing_infos()

    # Find the routing information
    r_info = routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, SPIKE_PARTITION_ID)

    n_cores = len(r_info.vertex.splitter.get_out_going_vertices(
            SPIKE_PARTITION_ID))

    # If there is 1 core, we don't use the core mask
    # If there is a virtual vertex, these also don't use core masks
    if n_cores == 1 or isinstance(pre_vertex, ApplicationVirtualVertex):
        return r_info, 0, 0

    mask_shift = r_info.n_bits_atoms
    core_mask = (2 ** get_n_bits(n_cores)) - 1
    return r_info, core_mask, mask_shift


def get_sources_for_target(app_vertex):
    """
    Get all the application vertex sources that will hit the given application
    vertex.

    :param AbstractPopulationVertex app_vertex: The vertex being targeted
    :return:
        A dict of source ApplicationVertex to list of source information
    :rtype: dict(ApplicationVertex, list(Source))
    """
    sources = defaultdict(list)
    for incoming in app_vertex.incoming_projections:
        pre_vertex, local_delay, delay_stage = get_delay_for_source(
            incoming)
        source = Source(incoming, local_delay, delay_stage)
        sources[pre_vertex].append(source)
    return sources


def get_first_and_last_slice(pre_vertex):
    """
    Get the first and last slice of an application vertex.

    :param ApplicationVertex pre_vertex: The source vertex
    :rtype: tuple(Slice, Slice) or tuple(MDSlice, MDSlice)
    """
    if isinstance(pre_vertex, ApplicationVirtualVertex):
        if len(pre_vertex.atoms_shape) == 1:
            full_slice = Slice(0, pre_vertex.n_atoms - 1)
            return full_slice, full_slice
        atoms_shape = pre_vertex.atoms_shape
        full_slice = MDSlice(
            0, pre_vertex.n_atoms - 1, atoms_shape, (0 for _ in atoms_shape),
            atoms_shape)
        return full_slice, full_slice
    m_vertices = list(pre_vertex.machine_vertices)
    return m_vertices[0].vertex_slice, m_vertices[-1].vertex_slice
