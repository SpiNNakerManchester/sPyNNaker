# Copyright (c) 2020-2023 The University of Manchester
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
from pacman.operations.partition_algorithms import splitter_partitioner
from data_specification import ReferenceContext


def spynnaker_splitter_partitioner():
    """ a splitter partitioner that's bespoke for spynnaker vertices.

    :return:
         The number of chips needed to satisfy this partitioning.
    :rtype: int
    """
    with ReferenceContext():
        return splitter_partitioner()
