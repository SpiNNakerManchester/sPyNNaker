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

from spynnaker.pyNN.models.recorder import Recorder as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class Recorder(_BaseClass):
    """
    .. deprecated:: 6.0
        Use :py:class:`spynnaker.pyNN.models.recorder.Recorder` instead.
    """
    # DO NOT DEFINE SLOTS! Multiple inheritance problems otherwise.
    # __slots__ = []

    def __init__(self, population, vertex):
        """
        :param population: the population to record for
        :type population: ~spynnaker.pyNN.models.populations.Population
        """
        moved_in_v6("spynnaker8.models.recorder",
                    "spynnaker.pyNN.models.recorder")
        super(Recorder, self).__init__(population, vertex)
