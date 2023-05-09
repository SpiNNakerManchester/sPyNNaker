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

"""
Synfirechain-like example
"""
import pytest
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
from pacman.exceptions import PacmanException

n_neurons = 200  # number of neurons in each population
runtime = 3000
neurons_per_core = 1
synfire_run = SynfireRunner()


class TestTooLow(BaseTestCase):
    """
    tests the run fails due to too small ram
    """

    def test_too_low(self):
        with pytest.raises(PacmanException):
            synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                               run_times=[runtime])


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime])
