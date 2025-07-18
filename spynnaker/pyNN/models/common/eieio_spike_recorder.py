# Copyright (c) 2015 The University of Manchester
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

import logging
import struct
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))
_TWO_WORDS = struct.Struct("<II")


class EIEIOSpikeRecorder(object):
    """
    Records spikes using EIEIO format.
    """
    __slots__ = ("__record", )

    def __init__(self) -> None:
        self.__record = False

    @property
    def record(self) -> bool:
        """
        If the recorder is set to record
        """
        return self.__record

    @record.setter
    def record(self, new_state: bool) -> None:
        """
        Old method assumed to be spikes.
        """
        self.__record = bool(new_state)
