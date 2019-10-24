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
from shutil import copyfile


def add_scripts(a_dir, prefix_len, test_file, exceptions, broken):
    for a_script in os.listdir(a_dir):
        if a_script in exceptions:
            continue
        script_path = os.path.join(a_dir, a_script)
        if os.path.isdir(script_path) and not a_script.startswith("."):
            add_scripts(script_path, prefix_len, test_file, exceptions, broken)
        if a_script.endswith(".py"):
            print(script_path)
            name = script_path[prefix_len:-3].replace(os.sep, "_")
            print(name)
            test_file.write("\n    def ")
            test_file.write(name)
            test_file.write("(self):\n        self.check_script(\"")
            test_file.write(os.path.abspath(script_path))
            if a_script in broken:
                test_file.write("\", True)\n\n    def test_")
            else:
                test_file.write("\", False)\n\n    def test_")
            test_file.write(name)
            test_file.write("(self):\n        self.runsafe(self.")
            test_file.write(name)
            test_file.write(")\n")


if __name__ == '__main__':
    tests_dir = os.path.dirname(__file__)
    spynnaker_integration_tests_dir = os.path.dirname(tests_dir)
    spynnaker_dir = os.path.dirname(spynnaker_integration_tests_dir)
    introlab_dir = os.path.join(spynnaker_dir, "IntroLab")
    # Jenkins appears to place Introlabs here
    if not os.path.exists(introlab_dir):
        parent_dir = os.path.dirname(spynnaker_dir)
        introlab_dir = os.path.join(parent_dir, "IntroLab")
    introlab_script = os.path.join(tests_dir, "intro_labs_auto_test.py")
    introlab_header = os.path.join(tests_dir, "intro_labs_header.py")
    copyfile(introlab_header, introlab_script)
    with open(introlab_script, "a") as introlab_file:
        introlab_file.write("# flake8: noqa\n")
        add_scripts(introlab_dir, len(introlab_dir)+1, introlab_file,
                    ["sudoku.py"], [])

    examples_dir = os.path.join(spynnaker_dir, "PyNN8Examples")
    # Jenkins appears to place PyNN8Examples here
    if not os.path.exists(examples_dir):
        parent_dir = os.path.dirname(spynnaker_dir)
        examples_dir = os.path.join(parent_dir, "PyNN8Examples")
    examples_script = os.path.join(tests_dir, "examples_auto_test.py")
    examples_header = os.path.join(tests_dir, "examples_header.py")
    copyfile(examples_header, examples_script)
    with open(examples_script, "a") as examples_file:
        examples_file.write("# flake8: noqa\n")
        add_scripts(examples_dir, len(examples_dir)+1, examples_file,
                    ["pushbot_ethernet_example.py"],
                    ["synfire_if_curr_exp_large_array.py",
                     "vogels_2011.py",
                     "vogels_2011_live.py"])
