# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from spinnaker_testbase import BaseTestCase


class TestNoJobDestory(BaseTestCase):

    def test_no_destory_file(self):
        warning_path = self.spinnman_exception_path()
        if os.path.exists(warning_path):
            with open(warning_path) as warning_file:
                warning_text = warning_file.read()
            print(warning_text)
            raise AssertionError(warning_text)
        warning_path = self.destory_path()
        if os.path.exists(warning_path):
            with open(warning_path) as warning_file:
                warning_text = warning_file.read()
            print(warning_text)
            raise AssertionError(warning_text)
