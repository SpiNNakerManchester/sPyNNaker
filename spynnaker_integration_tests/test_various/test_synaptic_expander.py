# Copyright (c) 2017 The University of Manchester
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

from collections import defaultdict
import functools
import math
from typing import Dict, List

import numpy
import pyNN.spiNNaker as p

from spinnman.exceptions import SpiNNManCoresNotInStateException
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.models.neuron import ConnectionHolder


def run_script() -> None:
    p.setup(1.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 3)

    inp = p.Population(10, p.SpikeSourceArray(spike_times=[1.0]),
                       label="SpikeSourceArray")
    out = p.Population(10, p.IF_curr_exp(), label="IF_curr_exp", seed=1235)
    out.record("spikes")

    param_projections = [
        (1.0, 1.0),
        (p.RandomDistribution("uniform", low=1.0, high=10.0), 2.0),
        (3.0, 17.0),
        (4.0, p.RandomDistribution("normal", mu=22.0, sigma=10.0)),
        (5.0, p.RandomDistribution(
            "normal_clipped", mu=22.0, sigma=10.0,
            low=5.0, high=32.0)),
        (6.0, p.RandomDistribution(
            "normal_clipped_to_boundary", mu=12.0, sigma=5.0,
            low=6.0, high=16.0)),
        (7.0, p.RandomDistribution("exponential", beta=5.0)),
        (8.0, p.RandomDistribution(
            "exponential_clipped", beta=2.0, low=0, high=3.0)),
    ]
    connectors = [
        (p.OneToOneConnector, functools.partial(check_one_to_one, 10)),
        (p.AllToAllConnector,
         functools.partial(check_all_to_all, 10)),
        (functools.partial(p.FixedProbabilityConnector, 0.5),
         functools.partial(check_fixed_prob, 10, 0.5)),
        (functools.partial(p.FixedTotalNumberConnector, 50,
                           with_replacement=True),
         functools.partial(check_fixed_total, 50)),
        (functools.partial(p.FixedTotalNumberConnector, 20,
                           with_replacement=False),
         functools.partial(check_fixed_total, 20))
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
        try:
            weights = proj.get("weight", "list", with_address=False)
            delays = proj.get("delay", "list", with_address=False)
            conns = proj.get([], "list")
            if not is_stdp:
                check_params(weight, weights)
            check_params(delay, delays)
            check(conns)
        except AssertionError as e:
            print(proj)
            print("Weight:", weight, ":-", weights)
            print("Delay:", delay, ":-", delays)
            p.end()
            raise e
    p.end()


def check_params(param: float, result: ConnectionHolder) -> None:
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


def check_one_to_one(n: int, conns: List[List[int]]) -> None:
    assert len(conns) == n
    assert all(pre == post for pre, post in conns)


def conns_by_pre(conns: List[List[int]]) -> Dict[int, List[int]]:
    cbp = defaultdict(list)
    for pre, post in conns:
        cbp[pre].append(post)
    return cbp


def conns_by_post(conns: List[List[int]]) -> Dict[int, List[int]]:
    cbp = defaultdict(list)
    for pre, post in conns:
        cbp[post].append(pre)
    return cbp


def check_all_to_all(n: int, conns: List[List[int]]) -> None:
    cbp = conns_by_pre(conns)
    assert len(cbp) == n
    for pre in cbp:
        assert numpy.array_equal(sorted(cbp[pre]), range(n))


def check_fixed_prob(n: int, prob: float, conns: List[List[int]]) -> None:
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


def check_fixed_total(total: int, conns: List[List[int]]) -> None:
    assert len(conns) == total


def run_bad_normal_clipping() -> None:
    p.setup(timestep=1.0)

    pop_1 = p.Population(4, p.IF_curr_exp(), label="pop_1")
    source = p.Population(4, p.SpikeSourceArray(spike_times=[0]), label="src")

    delays = p.RandomDistribution(
        "normal_clipped", mu=20, sigma=1, low=1, high=6)

    p.Projection(source, pop_1, p.AllToAllConnector(),
                 synapse_type=p.StaticSynapse(weight=5, delay=delays))

    p.run(10)

    p.end()


class TestSynapticExpander(BaseTestCase):

    def test_script(self) -> None:
        self.runsafe(run_script)

    def test_bad_normal_clipping(self) -> None:
        with self.assertRaises(SpiNNManCoresNotInStateException):
            run_bad_normal_clipping()


if __name__ == "__main__":
    run_script()
