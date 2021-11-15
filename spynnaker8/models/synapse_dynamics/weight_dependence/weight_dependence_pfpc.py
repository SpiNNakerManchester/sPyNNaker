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
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependencePFPC as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class WeightDependencePFPC(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence.WeightDependencePFPC`
        instead.
    """
    __slots__ = []

    def __init__(self, w_min=0.0, w_max=1.0, pot_alpha=0.01):
        r"""
        :param float w_min: :math:`w_\mathrm{min}`
        :param float w_max: :math:`w_\mathrm{max}`
        :param float pot_alpha: :math:`pot_\mathrm{alpha}`
        """
        moved_in_v6("spynnaker8.models.synapse_dynamics.weight_dependence"
                    ".WeightDependencePFPC",
                    "spynnaker.pyNN.models.neuron.plasticity.stdp."
                    "weight_dependence.WeightDependencePFPC")
        super(WeightDependencePFPC, self).__init__(
            w_min=w_min, w_max=w_max, pot_alpha=pot_alpha)
