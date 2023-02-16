# Copyright (c) 2017 The University of Manchester
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

from spynnaker.pyNN.models.neuron.builds import IFCurrExpBase
from spynnaker.pyNN.models.populations.population import Population
import pyNN.spiNNaker as sim

# NO unittest_step as sim.setup call is needed before creating a Population


def test_selector():
    sim.setup()
    model = IFCurrExpBase()
    pop_1 = Population(
        size=5, label="Test", cellclass=model,
        structure=None, initial_values={})
    pop_1.set(tau_m=2)
    values = pop_1.get("tau_m")
    assert [2, 2, 2, 2, 2] == values
    values = pop_1[1:3].get("tau_m")
    assert [2, 2] == values
    pop_1[1:3].set(tau_m=3)
    values = pop_1.get("tau_m")
    assert [2, 3, 3, 2, 2] == values
    values = pop_1.get(["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0, -50.0, -50.0] == values["v_thresh"]
    values = pop_1[1, 3, 4].get(["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0] == values["v_thresh"]


def test_round():
    sim.setup()
    model = IFCurrExpBase()
    pop_1 = Population(
        size=4.999999, label="Test", cellclass=model,
        structure=None, initial_values={})
    assert pop_1.size == 5
