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

from enum import Enum
from spynnaker.pyNN.protocols import RetinaKey


class PushBotRetinaResolution(Enum):
    """ Resolutions supported by the pushbot retina device
    """

    #: The native resolution
    NATIVE_128_X_128 = RetinaKey.NATIVE_128_X_128
    #: Down sampled 4 (:math:`2 \times 2`) pixels to 1
    DOWNSAMPLE_64_X_64 = RetinaKey.DOWNSAMPLE_64_X_64
    #: Down sampled 16 (:math:`4 \times 4`) pixels to 1
    DOWNSAMPLE_32_X_32 = RetinaKey.DOWNSAMPLE_32_X_32
    #: Down sampled 64 (:math:`8 \times 8`) pixels to 1
    DOWNSAMPLE_16_X_16 = RetinaKey.DOWNSAMPLE_16_X_16
