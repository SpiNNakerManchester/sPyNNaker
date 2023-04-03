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

import distutils.dir_util
from setuptools import setup
import os
import sys


if __name__ == '__main__':
    # Repeated installs assume files have not changed
    # https://github.com/pypa/setuptools/issues/3236
    if len(sys.argv) > 0 and sys.argv[1] == 'egg_info':
        # on the first call to setpy.py remove files left by previous install
        this_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(this_dir, "build")
        if os.path.isdir(build_dir):
            distutils.dir_util.remove_tree(build_dir)
        egg_dir = os.path.join(this_dir, "sPyNNaker.egg-info")
        if os.path.isdir(egg_dir):
            distutils.dir_util.remove_tree(egg_dir)
    setup()
