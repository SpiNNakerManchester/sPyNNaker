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
Script to demo why some connectors not tested virtually.

They do on machine generation so guess what they need!
"""
import spynnaker8 as sim
sim.setup(1.0)

pop1 = sim.Population(5, sim.IF_curr_exp(), {}, label="pop")
pop2 = sim.Population(4, sim.IF_curr_exp(), {}, label="pop")
synapse_type = sim.StaticSynapse(weight=5, delay=1)
# connector = sim.FromListConnector([[0,0,5,5]])
connector = sim.OneToOneConnector()

# connector = sim.FixedTotalNumberConnector(10, with_replacement=False)
# connector = sim.AllToAllConnector()

projection = sim.Projection(
    pop1, pop2, connector, synapse_type=synapse_type)
sim.run(10)
weights = projection.get(["weight"], "list")
try:
    print(weights)
except Exception as ex:
    print(ex)
sim.end()
