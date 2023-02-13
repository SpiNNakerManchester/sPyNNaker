# Copyright (c) 2015-2023 The University of Manchester
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
from spynnaker.pyNN.models.populations import Assembly as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class Assembly(_BaseClass):
    """
    A group of neurons, may be heterogeneous, in contrast to a Population
    where all the neurons are of the same type.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.populations.Assembly` instead.
    """

    def __init__(self, *populations, **kwargs):
        """
        :param populations:
            the populations or views to form the assembly out of
        :type populations: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        :param kwargs: may contain `label` (a string describing the assembly)
        """
        moved_in_v6("spynnaker8.models.populations.Assembly",
                    "spynnaker.pyNN.models.populations.Assembly")
        super(Assembly, self).__init__(*populations, **kwargs)
