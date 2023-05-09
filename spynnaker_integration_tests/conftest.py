# Copyright (c) 2023 The University of Manchester
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

import pytest
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
import pyNN.spiNNaker as sim


@pytest.fixture(autouse=True)
def check_end_is_called(request):
    """ Fixture for all tests, to make sure end is used!
    """
    yield
    # If we never setup or we are currently shut down, we are ok
    if not SpynnakerDataView.is_setup() or SpynnakerDataView().is_shutdown():
        return
    try:
        sim.end()
    except Exception:  # pylint: disable=broad-except
        # Ignore anything that comes from this
        pass
    raise Exception(f"Simulation has not been stopped in {request.function}!")
