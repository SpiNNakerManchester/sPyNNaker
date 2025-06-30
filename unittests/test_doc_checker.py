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

from spinn_utilities.config_setup import unittest_setup
from spinn_utilities.testing.docs_checker import DocsChecker


class TestCfgChecker(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    def test_doc_checks(self) -> None:
        class_file = sys.modules[self.__module__].__file__
        assert class_file is not None
        abs_class_file = os.path.abspath(class_file)
        unittest_dir = os.path.dirname(abs_class_file)
        repo_dir = os.path.dirname(unittest_dir)
        checker = DocsChecker(
            check_init=False, check_short=False, check_params=False)
        checker.check_dir(repo_dir)
        checker.check_no_errors()
