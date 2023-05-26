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
from spynnaker.pyNN.models.neural_projections.connectors import (
    ArrayConnector as _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class ArrayConnector(_BaseClass):
    """
    Make connections using an array of integers based on the IDs
    of the neurons in the pre- and post-populations.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.ArrayConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, array, safe=True, callback=None, verbose=False):
        """
        :param array: an array of integers
        :type array: ~numpy.ndarray(2, ~numpy.uint8)
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        moved_in_v6("spynnaker8.models.connectors.ArrayConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".ArrayConnector")
        super().__init__(
            array=array, safe=safe, callback=callback, verbose=verbose)
