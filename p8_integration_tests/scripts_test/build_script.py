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
import platform
from shutil import copyfile
import sys


def add_scripts(a_dir, prefix_len, test_file, exceptions, broken):
    for a_script in os.listdir(a_dir):
        if a_script in exceptions:
            continue
        script_path = os.path.join(a_dir, a_script)
        if os.path.isdir(script_path) and not a_script.startswith("."):
            add_scripts(script_path, prefix_len, test_file, exceptions, broken)
        if a_script.endswith(".py") and a_script != "__init__.py":
            name = script_path[prefix_len:-3].replace(os.sep, "_")
            test_file.write("\n    def ")
            test_file.write(name)
            test_file.write("(self):\n        self.check_script(\"")
            the_path = os.path.abspath(script_path)
            # As the paths are written to strings in files Windows needs help!
            if platform.system() == "Windows":
                the_path = the_path.replace("\\", "/")
            test_file.write(the_path)
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
    p8_integration_tests_dir = os.path.dirname(tests_dir)
    spynnaker8_dir = os.path.dirname(p8_integration_tests_dir)
    introlab_dir = os.path.join(spynnaker8_dir, "IntroLab")
    # Jenkins appears to place Introlabs here
    if not os.path.exists(introlab_dir):
        parent_dir = os.path.dirname(spynnaker8_dir)
        introlab_dir = os.path.join(parent_dir, "IntroLab")
    introlab_script = os.path.join(tests_dir, "intro_labs_auto_test.py")
    introlab_header = os.path.join(tests_dir, "intro_labs_header.py")
    copyfile(introlab_header, introlab_script)
    exceptions = ["sudoku.py"]
    # Lazy boolean distinction based on presence or absence of a parameter
    if len(sys.argv) > 1:  # 1 is the script name
        # Skip the known long ones
        exceptions.append("balanced_random.py")  # 115 seconds
    with open(introlab_script, "a") as introlab_file:
        introlab_file.write("# flake8: noqa\n")
        add_scripts(introlab_dir, len(introlab_dir)+1, introlab_file,
                    exceptions, [])
    examples_dir = os.path.join(spynnaker8_dir, "PyNN8Examples")
    # Jenkins appears to place PyNN8Examples here
    if not os.path.exists(examples_dir):
        parent_dir = os.path.dirname(spynnaker8_dir)
        examples_dir = os.path.join(parent_dir, "PyNN8Examples")
    examples_script = os.path.join(tests_dir, "examples_auto_test.py")
    examples_header = os.path.join(tests_dir, "examples_header.py")
    copyfile(examples_header, examples_script)
    exceptions = ["pushbot_ethernet_example.py"]
    # Lazy boolean distinction based on presence or absence of a parameter
    if len(sys.argv) > 1:  # 1 is the script name
        # Skip the known long ones
        exceptions.append("stdp_triplet.py")
        # exceptions.append("balanced_random_live_rate.py")  # 125 seconds
        # exceptions.append("stdp_curve.py")  # 118 seconds
        # exceptions.append("stdp_curve_cond.py")  # 121 seconds
        exceptions.append("vogels_2011.py")  # 698 seconds
        # binary fail to compile
        exceptions.append("structural_plasticity_with_stdp_2d.py")

    with open(examples_script, "a") as examples_file:
        examples_file.write("# flake8: noqa\n")
        add_scripts(examples_dir, len(examples_dir)+1, examples_file,
                    exceptions, [])
