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

from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


class TestDoNotAllowViolate(BaseTestCase):
    """
    Tests that running too fast needs to be specifically allowed
    """

    # NO unittest_setup() as sim.setup is called

    def test_do_not_allow_violate(self):
        with self.assertRaises(ConfigurationException):
            sim.setup()   # remember pynn default is 0.1
