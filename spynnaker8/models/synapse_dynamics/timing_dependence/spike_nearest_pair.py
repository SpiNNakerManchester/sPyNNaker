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
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikeNearestPair as
    _BaseClass)

_defaults = _BaseClass.default_parameters
logger = logging.getLogger(__name__)


class TimingDependenceSpikeNearestPair(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence.TimingDependenceSpikeNearestPair`
        instead.
    """
    __slots__ = []

    def __init__(
            self, tau_plus=_defaults['tau_plus'],
            tau_minus=_defaults['tau_minus'],
            A_plus=0.01, A_minus=0.01):
        r"""
        :param float tau_plus: :math:`\tau_+`
        :param float tau_minus: :math:`\tau_-`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        super(TimingDependenceSpikeNearestPair, self).__init__(
            tau_plus=tau_plus, tau_minus=tau_minus,
            A_plus=A_plus, A_minus=A_minus)
        logger.warning(
            "please use spynnaker.pyNN.models.neuron.plasticity.stdp."
            "timing_dependence.TimingDependenceSpikeNearestPair instead")
