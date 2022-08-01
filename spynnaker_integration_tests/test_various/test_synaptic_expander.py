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
from spinnman.exceptions import SpiNNManCoresNotInStateException
import functools
from spinnaker_testbase import BaseTestCase
import numpy
from pyNN.random import NumpyRNG
from collections import defaultdict
import math


def run_script():
    p.setup(1.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 3)

    inp = p.Population(10, p.SpikeSourceArray(spike_times=[1.0]),
                       label="SpikeSourceArray")
    out = p.Population(10, p.IF_curr_exp(), label="IF_curr_exp")
    out.record("spikes")

    rng = NumpyRNG(seed=1235)
    param_projections = [
        (1.0, 1.0),
        (p.RandomDistribution("uniform", low=1.0, high=10.0, rng=rng), 2.0),
        (3.0, 17.0),
        (4.0, p.RandomDistribution("normal", mu=22.0, sigma=10.0, rng=rng)),
        (5.0, p.RandomDistribution(
            "normal_clipped", mu=22.0, sigma=10.0,
            low=5.0, high=32.0, rng=rng)),
        (6.0, p.RandomDistribution(
            "normal_clipped_to_boundary", mu=12.0, sigma=5.0,
            low=6.0, high=16.0, rng=rng)),
        (7.0, p.RandomDistribution("exponential", beta=2.0, rng=rng)),
    ]
    connectors = [
        (p.OneToOneConnector, functools.partial(check_one_to_one, 10)),
        (p.AllToAllConnector,
         functools.partial(check_all_to_all, 10, True)),
        (functools.partial(p.AllToAllConnector,
                           allow_self_connections=False),
         functools.partial(check_all_to_all, 10, False)),
        (functools.partial(p.FixedProbabilityConnector, 0.5),
         functools.partial(check_fixed_prob, 10, 0.5, 3)),
        (functools.partial(p.FixedTotalNumberConnector, 50,
                           with_replacement=True),
         functools.partial(check_fixed_total, 10, 50)),
        (functools.partial(p.FixedTotalNumberConnector, 20,
                           with_replacement=False),
         functools.partial(check_fixed_total, 10, 20))
    ]

    projs = list()
    for weight, delay in param_projections:
        for connector, check in connectors:
            conn = connector()
            projs.append((
                weight, delay, conn, False, p.Projection(
                    inp, out, conn,
                    p.StaticSynapse(weight=weight, delay=delay)),
                check))
            projs.append((
                weight, delay, conn, True, p.Projection(
                    inp, out, conn,
                    p.STDPMechanism(
                        p.SpikePairRule(), p.AdditiveWeightDependence(),
                        weight=weight, delay=delay)),
                check))

    p.run(10)

    for weight, delay, connector, is_stdp, proj, check in projs:
        weights = proj.get("weight", "list", with_address=False)
        delays = proj.get("delay", "list", with_address=False)
        conns = proj.get([], "list")
        if not is_stdp:
            check_params(weight, weights)
        check_params(delay, delays)
        check(conns)

    p.end()


def check_params(param, result):
    if not isinstance(param, p.RandomDistribution):
        assert all(param == value for value in result)
    else:
        # Check the values are "random" (yes I know they might be the same,
        # but the chances are quite small!)
        minimum = numpy.amin(result)
        maximum = numpy.amax(result)
        assert minimum != maximum

        if "low" in param.parameters:
            assert param.parameters["low"] <= minimum
        if "high" in param.parameters:
            assert param.parameters["high"] >= maximum


def check_one_to_one(n, conns):
    assert len(conns) == n
    assert all(pre == post for pre, post in conns)


def conns_by_pre(conns):
    cbp = defaultdict(list)
    for pre, post in conns:
        cbp[pre].append(post)
    return cbp


def conns_by_post(conns):
    cbp = defaultdict(list)
    for pre, post in conns:
        cbp[post].append(pre)
    return cbp


def check_all_to_all(n, allow_self, conns):
    cbp = conns_by_pre(conns)
    assert len(cbp) == n
    for pre in cbp:
        if allow_self:
            assert numpy.array_equal(sorted(cbp[pre]), range(n))
        else:
            assert (numpy.array_equal(
                sorted(cbp[pre]),
                [i for i in range(n) if i != pre]))


def check_fixed_prob(n, prob, n_per_core, conns):
    cbpre = conns_by_pre(conns)
    cbpost = conns_by_post(conns)
    expected = n * prob
    error = math.sqrt(expected)
    avgpre = sum(len(cbpre[pre]) for pre in cbpre) / float(n)
    avgpost = sum(len(cbpost[post]) for post in cbpost) / float(n)
    assert avgpre >= (expected - error)
    assert avgpre <= (expected + error)
    assert avgpost >= (expected - error)
    assert avgpost <= (expected + error)


def check_fixed_total(n, total, conns):
    assert len(conns) == total


def run_bad_normal_clipping():
    p.setup(timestep=1.0)

    pop_1 = p.Population(4, p.IF_curr_exp(), label="pop_1")
    input = p.Population(4, p.SpikeSourceArray(spike_times=[0]), label="input")

    delays = p.RandomDistribution(
        "normal_clipped", mu=20, sigma=1, low=1, high=6)

    p.Projection(input, pop_1, p.AllToAllConnector(),
                 synapse_type=p.StaticSynapse(weight=5, delay=delays))

    p.run(10)

    p.end()


class TestSynapticExpander(BaseTestCase):

    def test_script(self):
        self.runsafe(run_script)

    def test_bad_normal_clipping(self):
        with self.assertRaises(SpiNNManCoresNotInStateException):
            run_bad_normal_clipping()


if __name__ == "__main__":
    run_script()
