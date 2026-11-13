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

"""Exercise the firmware row scheduler without a SpiNNaker board."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_firmware_scheduler(tmp_path: Path) -> None:
    compiler = shutil.which("cc")
    if compiler is None:
        pytest.skip("A host C compiler is required")

    test = Path(__file__).with_suffix(".c")
    source = (test.parents[2] / "neural_modelling" / "src" / "neuron" /
              "plasticity" / "stdp")
    executable = tmp_path / "stdp_update_schedule"
    subprocess.run([
        compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
        "-I", str(source), str(test), str(source / "stdp_update_schedule.c"),
        "-o", str(executable)
    ], check=True, timeout=30)
    subprocess.run([str(executable)], check=True, timeout=5)
