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
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():
    p.setup(1.0)
    n_neurons = 2

    pop_a = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[10, 20, 50],
        starts=[0, 500, 1000]),
        label="pop_a")
    pop_a.record("spikes")

    pop_b = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[[1, 2, 5], [10, 20, 50]],
        starts=[0, 500, 1000]),
        label="pop_b")
    pop_b.record("spikes")

    pop_c = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[10, 20, 50],
        starts=[10, 600, 1200],
        durations=[500, 500, 500]),
        label="pop_c")
    pop_c.record("spikes")

    pop_d = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[[1, 2, 5], [10, 20, 50]],
        starts=[0, 500, 1000],
        durations=[500, 400, 300]),
        label="pop_d")
    pop_d.record("spikes")

    pop_e = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[[1, 2, 5], [10, 20, 50]],
        starts=[[0, 500, 1000], [100, 600, 1100]],
        durations=[400, 300, 200]),
        label="pop_e")
    pop_e.record("spikes")

    pop_f = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[[1, 2, 5], [10, 20, 50]],
        starts=[[0, 500, 1000], [100, 600, 1100]],
        durations=[[400, 300, 200], [300, 200, 100]]),
        label="pop_f")
    pop_f.record("spikes")

    pop_g = p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
        rates=[[1, 2, 5], [10, 50]],
        starts=[[0, 100, 200], [200, 300]]),
        label="pop_g")
    pop_g.record("spikes")

    pop_h = p.Population(n_neurons, p.SpikeSourcePoisson(rate=1),
                         label="pop_h")
    pop_h.record("spikes")

    pop_i = p.Population(n_neurons, p.SpikeSourcePoisson(rate=1, start=100),
                         label="pop_i")
    pop_i.record("spikes")

    pop_j = p.Population(n_neurons, p.SpikeSourcePoisson(rate=[1, 10]),
                         label="pop_j")
    pop_j.record("spikes")

    pop_k = p.Population(
        n_neurons, p.SpikeSourcePoisson(rate=1, start=[0, 500]), label="pop_k")
    pop_k.record("spikes")

    pop_l = p.Population(
        n_neurons, p.SpikeSourcePoisson(rate=1, start=10, duration=500),
        label="pop_l")
    pop_l.record("spikes")

    pop_m = p.Population(n_neurons, p.SpikeSourcePoisson(
        rate=[1, 10], start=[0, 500], duration=500),
        label="pop_m")
    pop_m.record("spikes")

    pop_n = p.Population(n_neurons, p.SpikeSourcePoisson(
        rate=[1, 10], start=[0, 500], duration=[500, 800]),
        label="pop_n")
    pop_n.record("spikes")

    pop_o = p.Population(
        n_neurons, p.SpikeSourcePoisson(rate=1, duration=500), label="pop_o")
    pop_o.record("spikes")

    p.run(2000)

    p.end()


class TestCreatePoissons(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        do_run()


if __name__ == '__main__':
    do_run()
