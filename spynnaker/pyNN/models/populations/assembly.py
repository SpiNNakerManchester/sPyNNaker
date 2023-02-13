# Copyright (c) 2017-2023 The University of Manchester
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

from pyNN import common as pynn_common


class Assembly(pynn_common.Assembly):
    """
    A group of neurons, may be heterogeneous, in contrast to a Population
    where all the neurons are of the same type.

    :param populations: the populations or views to form the assembly out of
    :type populations: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param kwargs: may contain `label` (a string describing the assembly)
    """
