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
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType
from .abstract_input_type import AbstractInputType
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

TIME_STEP = "time_step"


class InputTypeDelta(AbstractInputType):
    """
    The delta input type.
    """
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            # scale_factor, calculated from timestep
            [Struct([(DataType.S1615, TIME_STEP)])],
            dict())

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[TIME_STEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        pass

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self) -> float:
        return 1.0
