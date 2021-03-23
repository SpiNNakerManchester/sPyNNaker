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

from spynnaker.pyNN.models.projection import Projection as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


# pylint: disable=abstract-method,too-many-arguments
class Projection(_BaseClass):
    """ sPyNNaker 8 projection class

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.projection.Projection` instead.
    """
    # pylint: disable=redefined-builtin
    __slots__ = [
        "__proj_label"]

    def __init__(
            self, pre_synaptic_population, post_synaptic_population,
            connector, synapse_type=None, source=None,
            receptor_type=None, space=None, label=None):
        """
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                pre_synaptic_population:
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                post_synaptic_population:
        :param AbstractConnector connector:
        :param AbstractStaticSynapseDynamics synapse_type:
        :param None source: Unsupported; must be None
        :param str receptor_type:
        :param ~pyNN.space.Space space:
        :param str label:
        """
        moved_in_v6("spynnaker8.models.projection",
                    "spynnaker.pyNN.models.projection")
        super(Projection, self).__init__(
            pre_synaptic_population, post_synaptic_population, connector,
            synapse_type, source, receptor_type, space, label)
