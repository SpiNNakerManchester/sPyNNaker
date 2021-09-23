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

from spinn_front_end_common.interface.interface_functions import (
    GraphDataSpecificationWriter)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neuron import SynapticManager
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.spike_source.rate_live_injector_vertex import \
    RateLiveInjectorVertex
from spynnaker.pyNN.models.spike_source.rate_source_live_vertex import \
    RateSourceLiveVertex


class SpynnakerDataSpecificationWriter(
        GraphDataSpecificationWriter):
    """ Executes data specification generation for sPyNNaker
    """

    __slots__ = ()

    def __call__(
            self, placements, hostname,
            report_default_directory, write_text_specs, machine,
            data_n_timesteps, graph_mapper=None):
        # pylint: disable=too-many-arguments

        delay_extensions = list()
        syn_vertices = list()
        neuron_vertices = list()
        rate_injectors = list()
        rate_sources = list()
        placement_order = list()
        for placement in placements.placements:
            associated_vertex = graph_mapper.get_application_vertex(
                placement.vertex)

            if isinstance(associated_vertex, DelayExtensionVertex):
                delay_extensions.append(placement)
            elif isinstance(associated_vertex, SynapticManager):
                syn_vertices.append(placement)
            elif isinstance(associated_vertex, AbstractPopulationVertex):
                neuron_vertices.append(placement)
            elif isinstance(associated_vertex, RateLiveInjectorVertex):
                rate_injectors.append(placement)
            elif isinstance(associated_vertex, RateSourceLiveVertex):
                rate_sources.append(placement)
            else:
                placement_order.append(placement)

        placement_order.extend(syn_vertices)
        placement_order.extend(neuron_vertices)
        placement_order.extend(delay_extensions)
        placement_order.extend(rate_injectors)
        placement_order.extend(rate_sources)

        return super(SpynnakerDataSpecificationWriter, self).__call__(
            placements, hostname, report_default_directory, write_text_specs,
            machine, data_n_timesteps, graph_mapper,
            placement_order)
