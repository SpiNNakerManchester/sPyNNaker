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

"""
.. warning::
    Using classes via this module is deprecated. Please use
    :py:mod:`spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence`
    instead.
"""

from .weight_dependence_additive import WeightDependenceAdditive
from .weight_dependence_multiplicative import WeightDependenceMultiplicative
from .weight_dependence_additive_triplet import WeightDependenceAdditiveTriplet
from .weight_dependence_pfpc import WeightDependencePFPC
from .weight_dependence_mfvn import WeightDependenceMFVN

__all__ = ["WeightDependenceAdditive", "WeightDependenceMultiplicative",
           "WeightDependenceAdditiveTriplet", "WeightDependencePFPC",
           "WeightDependenceMFVN"]
