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
from pyNN.standardmodels.synapses import StaticSynapse as PyNNStaticSynapse
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic as
    _BaseClass)
logger = logging.getLogger(__name__)


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
        super(SynapseDynamicsStatic, self).__init__(weight, delay)
        logger.warning(
            "please use spynnaker.pyNN.models.neuron.synapse_dynamics."
            "SynapseDynamicsStatic instead")
