# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    AbstractSynapseStructure)


class SynapseStructureWeightAccumulator(AbstractSynapseStructure):
    __slots__ = ()

    @overrides(AbstractSynapseStructure.get_n_half_words_per_connection)
    def get_n_half_words_per_connection(self):
        return 2

    @overrides(AbstractSynapseStructure.get_weight_half_word)
    def get_weight_half_word(self):
        return 0
