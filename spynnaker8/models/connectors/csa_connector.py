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
    CSAConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class CSAConnector(_BaseClass):
    """
    A CSA (*Connection Set Algebra*, Djurfeldt 2012) connector.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.CSAConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, cset, safe=True, callback=None, verbose=False):
        """
        :param cset: a connection set description
        :type cset: csa.connset.CSet
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors.CSAConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".CSAConnector")
        super().__init__(
            cset=cset, safe=safe, callback=callback, verbose=verbose)
