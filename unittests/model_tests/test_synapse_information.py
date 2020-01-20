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


from spynnaker.pyNN.models.neural_projections.synapse_information import (
    SynapseInformation)
from unittests.mocks import MockSimulator


def test_rounding():
    MockSimulator.setup()
    weight = 1.0
    delay = 1.0
    synapse_info = SynapseInformation(
        connector="Stub", pre_population="Stub",
        post_population="Stub",
        prepop_is_view=False, postpop_is_view=False, rng=None,
        synapse_dynamics="Stub", synapse_type="Stub", weights=weight,
        delays=[delay])
    assert (1.0 == synapse_info.rounded_delays_in_ms(timestep_in_us=1000))
