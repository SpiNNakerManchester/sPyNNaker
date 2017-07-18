from enum import Enum
from spynnaker.pyNN.protocols import RetinaKey


class PushBotRetinaResolution(Enum):

    NATIVE_128_X_128 = RetinaKey.NATIVE_128_X_128
    DOWNSAMPLE_64_X_64 = RetinaKey.DOWNSAMPLE_64_X_64
    DOWNSAMPLE_32_X_32 = RetinaKey.DOWNSAMPLE_32_X_32
    DOWNSAMPLE_16_X_16 = RetinaKey.DOWNSAMPLE_16_X_16
