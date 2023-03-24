# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Connectors are objects that describe how neurons in
:py:class:`~spynnaker.pyNN.models.populations.Population`\ s
are connected to each other.

.. deprecated:: 6.0
    Use :py:mod:`spynnaker.pyNN.models.neural_projections.connectors` instead.
"""

from .all_to_all_connector import AllToAllConnector
from .array_connector import ArrayConnector
from .csa_connector import CSAConnector
from .distance_dependent_prob_connector import (
    DistanceDependentProbabilityConnector)
from .fixed_number_post_connector import FixedNumberPostConnector
from .fixed_number_pre_connector import FixedNumberPreConnector
from .fixed_prob_connector import FixedProbabilityConnector
from .from_file_connector import FromFileConnector
from .from_list_connector import FromListConnector
from .index_based_prob_connector import IndexBasedProbabilityConnector
from .multapse_connector import MultapseConnector
from .one_to_one_connector import OneToOneConnector
from .small_world_connector import SmallWorldConnector
from .kernel_connector_connector import KernelConnector

__all__ = ["AllToAllConnector", "ArrayConnector", "CSAConnector",
           "DistanceDependentProbabilityConnector", "FixedNumberPostConnector",
           "FixedNumberPreConnector", "FixedProbabilityConnector",
           "FromFileConnector", "FromListConnector",
           "IndexBasedProbabilityConnector", "MultapseConnector",
           "OneToOneConnector", "SmallWorldConnector", "KernelConnector"]
