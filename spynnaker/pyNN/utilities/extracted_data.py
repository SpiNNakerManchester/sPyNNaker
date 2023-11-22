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

from collections import defaultdict


class ExtractedData(object):
    """
    Data holder for all synaptic data being extracted in parallel.
    """
    # @Chimp: play here to hearts content.

    __slots__ = ("__data", )

    def __init__(self):
        self.__data = defaultdict(dict)

    def get(self, projection, attribute):
        """
        Allow getting data from a given projection and attribute.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            the projection data was extracted from
        :param attribute: the attribute to retrieve
        :type attribute: list(int) or tuple(int) or None
        :return: the attribute data in a connection holder
        :rtype: ConnectionHolder
        """
        if projection in self.__data:
            if attribute in self.__data[projection]:
                return self.__data[projection][attribute]
        return None

    def set(self, projection, attribute, data):
        """
        Allow the addition of data from a projection and attribute.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            the projection data was extracted from
        :param attribute: the attribute to store
        :type attribute: list(int) or tuple(int) or None
        :param ConnectionHolder data:
            attribute data in a connection holder
        """
        self.__data[projection][attribute] = data
