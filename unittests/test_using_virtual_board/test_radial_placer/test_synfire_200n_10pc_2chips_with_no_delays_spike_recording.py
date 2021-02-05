#!/usr/bin/python

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

"""
Synfirechain-like example
"""

from pacman.model.constraints.placer_constraints import (
    RadialPlacementFromChipConstraint)
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

nNeurons = 200  # number of neurons in each population
constraint = RadialPlacementFromChipConstraint(3, 3)
delay = 1
neurons_per_core = 10
record_v = False
record_gsyn = False
synfire_run = SynfireRunner()


class Synfire200n10pc2chipsWithNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        pass
    #    synfire_run.do_run(nNeurons, delay=delay,
    #                       neurons_per_core=neurons_per_core,
    #                       constraint=constraint,
    #                       record_v=record_v,
    #                       record_gsyn_exc=record_gsyn,
    #                       record_gsyn_inh=record_gsyn)


if __name__ == '__main__':
    x = Synfire200n10pc2chipsWithNoDelaysSpikeRecording()
    x.test_run()
