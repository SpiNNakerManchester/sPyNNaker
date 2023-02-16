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
