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
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    DURATION_FOREVER)
from spinnaker_testbase import BaseTestCase
import scipy
import numpy


def array(value):
    return numpy.array(value).reshape(-1)


def variable_rate_options():
    """ Test the various options that can be passed to a variable rate Poisson
    """
    p.setup(1.0)
    n_neurons = 2
    run_time = 20000
    seed = 0

    pops = list()

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[10, 20, 50],
            starts=[0, 5000, 10000]),
            label="pop_a",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[[1, 2, 5], [10, 20, 50]],
            starts=[0, 5000, 10000]),
            label="pop_b",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[10, 20, 50],
            starts=[100, 6000, 12000],
            durations=[5000, 5000, 5000]),
            label="pop_c",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[[1, 2, 5], [10, 20, 50]],
            starts=[0, 5000, 10000],
            durations=[5000, 4000, 3000]),
            label="pop_d",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[[1, 2, 5], [10, 20, 50]],
            starts=[[0, 5000, 10000], [1000, 6000, 11000]],
            durations=[4000, 3000, 2000]),
            label="pop_e",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[[1, 2, 5], [10, 20, 50]],
            starts=[[0, 5000, 10000], [1000, 6000, 11000]],
            durations=[[4000, 3000, 2000], [3000, 2000, 1000]]),
            label="pop_f",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.extra_models.SpikeSourcePoissonVariable(
            rates=[[1, 2, 5], [10, 50]],
            starts=[[0, 1000, 2000], [2000, 3000]]),
            label="pop_g",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(rate=1),
                     label="pop_h", additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(rate=1, start=100),
                     label="pop_i", additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(rate=[1, 10]),
                     label="pop_j", additional_parameters={"seed": seed + 1}))

    pops.append(
        p.Population(
            n_neurons, p.SpikeSourcePoisson(rate=1, start=[0, 5000]),
            label="pop_k",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(
            n_neurons, p.SpikeSourcePoisson(rate=1, start=10, duration=5000),
            label="pop_l",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(
            rate=[1, 10], start=[0, 5000], duration=5000),
            label="pop_m",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(
            rate=[1, 10], start=[0, 5000], duration=[5000, 8000]),
            label="pop_n",
            additional_parameters={"seed": seed}))

    pops.append(
        p.Population(n_neurons, p.SpikeSourcePoisson(
            rate=1, duration=5000), label="pop_o"))

    for pop in pops:
        pop.record("spikes")

    p.run(run_time)

    all_spikes = list()
    for pop in pops:
        all_spikes.append(pop.get_data("spikes").segments[0].spiketrains)
    p.end()

    for pop, spikes in zip(pops, all_spikes):
        print("")
        print("==============================")
        print(pop.label)
        if isinstance(pop.celltype, p.SpikeSourcePoisson):
            names = ["rate", "start", "duration"]
        else:
            names = ["rates", "starts", "durations"]

        for i in range(n_neurons):
            output = ""
            values = []
            for name in names:
                output += "{}: {{}}; ".format(name)
                values.append(pop.get(name)[i])
            print(output.format(*values))
            print(spikes[i])

            # Check the rates
            rates, starts, durations = (
                array(values[0]), array(values[1]), array(values[2]))
            ends = list()
            for j, (start, duration) in enumerate(zip(starts, durations)):
                if duration == DURATION_FOREVER and (j + 1) >= len(starts):
                    ends.append(run_time)
                elif duration == DURATION_FOREVER:
                    ends.append(starts[j + 1])
                else:
                    ends.append(start + duration)
            for rate, start, end in zip(rates, starts, ends):
                rate_spikes = spikes[i][(spikes[i] >= start) &
                                        (spikes[i] < end)]
                expected = (rate / 1000.0) * (end - start)
                tolerance = scipy.stats.poisson.ppf(0.99, expected) - expected
                n_spikes = len(rate_spikes)
                print("Received {} spikes, expected {} spikes"
                      " (with tolerance {}) for rate {}"
                      " for duration {}".format(
                          n_spikes, expected, tolerance, rate, (end - start)))
                assert n_spikes >= (expected - tolerance)
                assert n_spikes <= (expected + tolerance)


def variable_rate_reset():
    """ Test the ways of changing rates and ensure that they don't change the\
        results
    """
    p.setup(1.0)
    pop = p.Population(100, p.extra_models.SpikeSourcePoissonVariable(
        rates=[1, 10, 100], starts=[0, 1000, 2000]),
        additional_parameters={"seed": 0})
    pop_2 = p.Population(100, p.SpikeSourcePoisson(rate=1),
                         additional_parameters={"seed": 0, "max_rate": 100})
    pop.record("spikes")
    pop_2.record("spikes")

    p.run(1000)
    spikes_pop_2_1 = pop_2.get_data("spikes")
    nump = [s.magnitude for s in spikes_pop_2_1.segments[0].spiketrains]
    numpy.savetxt("spikesp2_1.txt", nump[0])
    pop_2.set(rate=10)
    p.run(1000)
    spikes_pop_2_2 = pop_2.get_data("spikes")
    nump = [s.magnitude for s in spikes_pop_2_2.segments[0].spiketrains]
    numpy.savetxt("spikesp2_2.txt", nump[0])
    pop_2.set(rate=100)
    p.run(1000)
    p.reset()
    p.run(3000)
    spikes_pop = pop.get_data("spikes")
    spikes_pop_2 = pop_2.get_data("spikes")
    p.end()

    spikes_1 = [s.magnitude for s in spikes_pop.segments[0].spiketrains]
    spikes_2 = [s.magnitude for s in spikes_pop.segments[1].spiketrains]
    spikes_p_2 = [s.magnitude for s in spikes_pop_2.segments[0].spiketrains]

    print(spikes_1)
    numpy.savetxt("spikes1.txt", spikes_1[0])
    print(spikes_2)
    numpy.savetxt("spikes2.txt", spikes_2[0])
    print(spikes_p_2)
    numpy.savetxt("spikesp2.txt", spikes_p_2[0])

    for s1, s2, s3 in zip(spikes_1, spikes_2, spikes_p_2):
        assert numpy.array_equal(s1, s2)
        assert numpy.array_equal(s2, s3)


def variable_rate_100us():
    """ Test that the source works at 0.1ms timesteps
    """
    rates = [1, 10, 100]
    starts = [0, 1000, 1500]
    ends = [1000, 1500, 2000]
    p.setup(0.1)
    pop = p.Population(100, p.extra_models.SpikeSourcePoissonVariable(
        rates=rates, starts=starts),
        additional_parameters={"seed": 0})
    pop.record("spikes")
    run_time = 2000
    p.run(run_time)

    spikes = pop.get_data("spikes").segments[0].spiketrains
    p.end()

    n_spikes = dict()
    for i in range(len(spikes)):
        for rate, start, end in zip(rates, starts, ends):
            rate_spikes = spikes[i][(spikes[i] >= start) &
                                    (spikes[i] < end)]
            if (rate, start, end) not in n_spikes:
                n_spikes[rate, start, end] = len(rate_spikes)
            else:
                n_spikes[rate, start, end] += len(rate_spikes)
    for rate, start, end in n_spikes:
        expected = (rate / 1000.0) * (end - start)
        tolerance = scipy.stats.poisson.ppf(0.99, expected) - expected
        n_spikes_rate = n_spikes[rate, start, end] / 100.0
        print("Received {} spikes, expected {} spikes"
              " (with tolerance {}) for rate {}"
              " for duration {}".format(
                  n_spikes_rate, expected, tolerance, rate, (end - start)))
        assert n_spikes_rate >= (expected - tolerance)
        assert n_spikes_rate <= (expected + tolerance)


class TestCreatePoissons(BaseTestCase):

    def test_variable_rate_options(self):
        self.runsafe(variable_rate_options)

    def test_rate_reset(self):
        self.runsafe(variable_rate_reset)

    def test_variable_rate_100us(self):
        self.runsafe(variable_rate_100us)


if __name__ == '__main__':
    variable_rate_options()
    # variable_rate_reset()
    # variable_rate_100us()
