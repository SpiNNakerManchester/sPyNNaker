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

import os
import sys
import unittest

from spinn_utilities.configs.config_checker import ConfigChecker
from spinn_utilities.configs.config_documentor import ConfigDocumentor

import spynnaker
from spynnaker.pyNN.config_setup import unittest_setup


class TestCfgChecker(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    def test_config_checks(self) -> None:
        unittests = os.path.dirname(__file__)
        parent = os.path.dirname(unittests)
        spynnaker_dir = spynnaker.__path__[0]
        spynnaker_it = os.path.join(parent, "spynnaker_integration_tests")
        ConfigChecker([spynnaker_dir, spynnaker_it, unittests]).check()

    def test_cfg_documentor(self) -> None:
        class_file = sys.modules[self.__module__].__file__
        assert class_file is not None
        abs_class_file = os.path.abspath(class_file)
        unittest_dir = os.path.dirname(abs_class_file)
        spynnaker_dir = os.path.dirname(unittest_dir)
        parent_dir = os.path.dirname(spynnaker_dir)
        target_dir = os.path.join(
            parent_dir,
            "SpiNNakerManchester.github.io", "spynnaker", "9.0.0")
        if os.path.exists(target_dir):
            target = os.path.join(target_dir, "cfg.md")
        else:
            print(f"Unable to find {target_dir}")
            target = os.path.join(unittest_dir, 'test.md')

        documentor = ConfigDocumentor()
        documentor.md_configs(target)
