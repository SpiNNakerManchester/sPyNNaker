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

from spynnaker.pyNN.models.neuron.builds import IFCurrExpBase
from spynnaker.pyNN.models.populations.population import Population
import spynnaker8


def test_selector():
    spynnaker8.setup()
    model = IFCurrExpBase()
    pop_1 = Population(
        size=5, label="Test", constraints=None, cellclass=model,
        structure=None, initial_values={})
    pop_1.set(tau_m=2)
    values = pop_1.get("tau_m")
    assert [2, 2, 2, 2, 2] == values
    values = pop_1._get_by_selector(slice(1, 3), "tau_m")
    assert [2, 2] == values
    pop_1.set_by_selector(slice(1, 3), "tau_m", 3)
    values = pop_1.get("tau_m")
    assert [2, 3, 3, 2, 2] == values
    values = pop_1.get(["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0, -50.0, -50.0] == values["v_thresh"]
    values = pop_1._get_by_selector([1, 3, 4], ["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0] == values["v_thresh"]


def test_round():
    spynnaker8.setup()
    model = IFCurrExpBase()
    pop_1 = Population(
        size=4.999999, label="Test", cellclass=model,
        constraints=None, structure=None, initial_values={})
    assert pop_1.size == 5
