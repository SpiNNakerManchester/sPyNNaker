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

import spynnaker as p
from spynnaker import RandomDistribution
import functools
from spynnaker_integration_tests.base_test_case import BaseTestCase
import numpy
from pyNN.random import NumpyRNG


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
        (RandomDistribution("uniform", low=1.0, high=10.0, rng=rng), 2.0),
        (3.0, 17.0),
        (4.0, RandomDistribution("normal", mu=22.0, sigma=10.0, rng=rng)),
        (5.0, RandomDistribution(
            "normal_clipped", mu=22.0, sigma=10.0,
            low=5.0, high=32.0, rng=rng)),
        (6.0, RandomDistribution(
            "normal_clipped_to_boundary", mu=12.0, sigma=5.0,
            low=6.0, high=16.0, rng=rng)),
        (7.0, RandomDistribution("exponential", beta=2.0, rng=rng)),
    ]
    connectors = [
        p.OneToOneConnector,
        p.AllToAllConnector,
        functools.partial(p.AllToAllConnector,
                          allow_self_connections=False),
        functools.partial(p.FixedProbabilityConnector, 0.5),
        functools.partial(p.FixedTotalNumberConnector, 50,
                          with_replacement=True),
        functools.partial(p.FixedTotalNumberConnector, 20,
                          with_replacement=False)
    ]

    projs = list()
    for weight, delay in param_projections:
        for connector in connectors:
            conn = connector()
            projs.append((weight, delay, conn, False, p.Projection(
                inp, out, conn,
                p.StaticSynapse(weight=weight, delay=delay))))
            projs.append((weight, delay, conn, True, p.Projection(
                inp, out, conn,
                p.STDPMechanism(
                    p.SpikePairRule(), p.AdditiveWeightDependence(),
                    weight=weight, delay=delay))))

    p.run(10)

    for weight, delay, connector, is_stdp, proj in projs:
        weights = proj.get("weight", "list", with_address=False)
        delays = proj.get("delay", "list", with_address=False)
        if not is_stdp:
            check_params(weight, weights)
        check_params(delay, delays)

    p.end()


def check_params(param, result):
    if not isinstance(param, RandomDistribution):
        assert(all(param == value for value in result))
    else:
        # Check the values are "random" (yes I know they might be the same,
        # but the chances are quite small!)
        minimum = numpy.amin(result)
        maximum = numpy.amax(result)
        assert(minimum != maximum)

        if "low" in param.parameters:
            assert(param.parameters["low"] <= minimum)
        if "high" in param.parameters:
            assert(param.parameters["high"] >= maximum)


class TestSynapticExpander(BaseTestCase):

    def test_script(self):
        self.runsafe(run_script)


if __name__ == "__main__":
    run_script()
