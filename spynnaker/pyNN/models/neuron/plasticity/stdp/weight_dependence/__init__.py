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

from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence
from .weight_dependence_additive import WeightDependenceAdditive
from .weight_dependence_multiplicative import WeightDependenceMultiplicative
from .weight_dependence_additive_triplet import WeightDependenceAdditiveTriplet

__all__ = ["AbstractHasAPlusAMinus", "AbstractWeightDependence",
           "WeightDependenceAdditive", "WeightDependenceMultiplicative",
           "WeightDependenceAdditiveTriplet"]
