# Copyright (c) 2021 The University of Manchester
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
from pyNN.standardmodels.synapses import StaticSynapse as PyNNStaticSynapse
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class SynapseDynamicsStatic(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.synapse_dynamics.SynapseDynamicsStatic`
        instead.
    """
    __slots__ = []

    def __init__(
            self, weight=PyNNStaticSynapse.default_parameters['weight'],
            delay=None):
        """
        :param float weight:
        :param delay:
        :type delay: float or None
        """
        moved_in_v6("spynnaker8.models.synapse_dynamics.SynapseDynamicsStatic",
                    "spynnaker.pyNN.models.neuron.synapse_dynamics"
                    ".SynapseDynamicsStatic")
        super(SynapseDynamicsStatic, self).__init__(weight, delay)
