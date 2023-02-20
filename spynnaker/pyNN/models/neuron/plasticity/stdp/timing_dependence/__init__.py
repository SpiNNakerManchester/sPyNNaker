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

from .abstract_timing_dependence import AbstractTimingDependence
from .timing_dependence_spike_pair import TimingDependenceSpikePair
from .timing_dependence_pfister_spike_triplet import (
    TimingDependencePfisterSpikeTriplet)
from .timing_dependence_recurrent import TimingDependenceRecurrent
from .timing_dependence_spike_nearest_pair import (
    TimingDependenceSpikeNearestPair)
from .timing_dependence_vogels_2011 import TimingDependenceVogels2011
from .timing_dependence_pfpc import TimingDependencePFPC
from .timing_dependence_mfvn import TimingDependenceMFVN

__all__ = [
    "AbstractTimingDependence", "TimingDependenceSpikePair",
    "TimingDependencePfisterSpikeTriplet", "TimingDependenceRecurrent",
    "TimingDependenceSpikeNearestPair", "TimingDependenceVogels2011",
    "TimingDependencePFPC", "TimingDependenceMFVN"
    ]
