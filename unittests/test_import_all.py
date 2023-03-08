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
import unittest
import spinn_utilities.package_loader as package_loader


class ImportAllModule(unittest.TestCase):

    # no unittest_setup to check all imports work without it

    def test_import_all(self):
        if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
            package_loader.load_module("spynnaker", remove_pyc_files=False)
        else:
            # Do a full stack cleanup
            package_loader.load_module(
                "spinn_utilities", remove_pyc_files=True)
            package_loader.load_module("spinn_machine", remove_pyc_files=True)
            package_loader.load_module("spinnman", remove_pyc_files=True)
            package_loader.load_module("pacman", remove_pyc_files=True)
            package_loader.load_module(
                "data_specification", remove_pyc_files=True)
            package_loader.load_module(
                "spalloc", remove_pyc_files=True)
            package_loader.load_module(
                "spinn_front_end_common", remove_pyc_files=True)
            # Test the files
            package_loader.load_module("spynnaker", remove_pyc_files=True)
