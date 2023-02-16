# Copyright (c) 2014 The University of Manchester
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

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
from .all_to_all_connector import AllToAllConnector
from .array_connector import ArrayConnector
from .csa_connector import CSAConnector
from .distance_dependent_probability_connector import (
    DistanceDependentProbabilityConnector)
from .fixed_number_post_connector import FixedNumberPostConnector
from .fixed_number_pre_connector import FixedNumberPreConnector
from .fixed_probability_connector import FixedProbabilityConnector
from .from_file_connector import FromFileConnector
from .from_list_connector import FromListConnector
from .index_based_probability_connector import IndexBasedProbabilityConnector
from .multapse_connector import MultapseConnector
from .one_to_one_connector import OneToOneConnector
from .small_world_connector import SmallWorldConnector
from .kernel_connector import KernelConnector
from .convolution_connector import ConvolutionConnector
from .pool_dense_connector import PoolDenseConnector

__all__ = ["AbstractConnector", "AbstractGenerateConnectorOnMachine",
           "AbstractGenerateConnectorOnHost", "AllToAllConnector",
           "ArrayConnector", "CSAConnector",
           "DistanceDependentProbabilityConnector", "FixedNumberPostConnector",
           "FixedNumberPreConnector", "FixedProbabilityConnector",
           "FromFileConnector",
           "FromListConnector", "IndexBasedProbabilityConnector",
           "KernelConnector", "ConvolutionConnector", "PoolDenseConnector",
           "MultapseConnector", "OneToOneConnector", "SmallWorldConnector"]
