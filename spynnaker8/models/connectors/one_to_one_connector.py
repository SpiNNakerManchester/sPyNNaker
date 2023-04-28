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
    OneToOneConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class OneToOneConnector(_BaseClass):
    """
    Where the pre- and postsynaptic populations have the same size, connect
    cell *i* in the presynaptic population to cell *i* in the postsynaptic
    population for all *i*.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.OneToOneConnector`
        instead.
    """
    __slots__ = []

    def __init__(self, safe=True, callback=None):
        """
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param callable callback: a function that will be called with the
            fractional progress of the connection routine. An example would
            be `progress_bar.set_level`.

            .. note::
                Not supported by sPyNNaker.
        """
        moved_in_v6("spynnaker8.models.connectors.OneToOneConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".OneToOneConnector")
        _BaseClass.__init__(self, safe=safe, callback=callback)
