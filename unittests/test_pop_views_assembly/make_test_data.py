# Copyright (c) 2017-2020 The University of Manchester
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

import numpy
import os
import shutil
from spinn_front_end_common.utilities.base_database import BaseDatabase
import pyNN.spiNNaker as sim
from spynnaker.pyNN.data import SpynnakerDataView


def make_data(do_view):
    sim.setup(timestep=1.0)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

    pop_1 = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
    input = sim.Population(5, sim.SpikeSourceArray(
        spike_times=[[0, 10, 20],
                     [1, 11, 21],
                     [2, 12, 22],
                     [3, 13, 23],
                     [4, 14, 24]]),
        label="input")
    sim.Projection(input, pop_1, sim.OneToOneConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    if do_view:
        pop_1[1, 2].record(["spikes", "v"])
    else:
        pop_1.record(["spikes", "v"])
    simtime = 35
    sim.run(simtime)

    if not do_view:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        neo = pop_1.get_data(variables=["spikes", "v"])
        spikes = neo.segments[0].spiketrains
        my_spikes = os.path.join(my_dir, "spikes.csv")
        numpy.savetxt(my_spikes, spikes, delimiter=",")
        print(spikes)
        v = neo.segments[0].filter(name='v')[0]
        my_v = os.path.join(my_dir, "v.csv")
        numpy.savetxt(my_v, v, delimiter=",")
        print(v)
    sim.end()

    run_buffer = BaseDatabase.default_database_file()
    my_dir = os.path.dirname(os.path.abspath(__file__))
    if do_view:
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
    else:
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
    shutil.copyfile(run_buffer, my_buffer)


make_data(True)
make_data(False)
