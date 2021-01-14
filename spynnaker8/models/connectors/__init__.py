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

r"""
Connectors are objects that describe how neurons in
:py:class:`~spynnaker8.models.populations.Population`\ s
are connected to each other.

.. deprecated:: 6.0
    Use :py:mod:`spynnaker.pyNN.models.neural_projections.connectors` instead.
"""

from .all_to_all import AllToAllConnector
from .array_connector import ArrayConnector
from .csa_connector import CSAConnector
from .distance_dependent_prob import DistanceDependentProbabilityConnector
from .fixed_number_post import FixedNumberPostConnector
from .fixed_number_pre import FixedNumberPreConnector
from .fixed_prob import FixedProbabilityConnector
from .from_file import FromFileConnector
from .from_list import FromListConnector
from .index_based_prob import IndexBasedProbabilityConnector
from .multapse import MultapseConnector
from .one_to_one import OneToOneConnector
from .small_world import SmallWorldConnector
from .kernel_connector import KernelConnector

__all__ = ["AllToAllConnector", "ArrayConnector", "CSAConnector",
           "DistanceDependentProbabilityConnector", "FixedNumberPostConnector",
           "FixedNumberPreConnector", "FixedProbabilityConnector",
           "FromFileConnector", "FromListConnector",
           "IndexBasedProbabilityConnector", "MultapseConnector",
           "OneToOneConnector", "SmallWorldConnector", "KernelConnector"]
