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
    :py:mod:`spynnaker.pyNN.models.neuron.synapse_dynamics` instead.
"""

from .synapse_dynamics_static import SynapseDynamicsStatic
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_structural_static import SynapseDynamicsStructuralStatic
from .synapse_dynamics_structural_stdp import SynapseDynamicsStructuralSTDP

__all__ = ["SynapseDynamicsStatic", "SynapseDynamicsSTDP",
           "SynapseDynamicsStructuralStatic", "SynapseDynamicsStructuralSTDP"]
