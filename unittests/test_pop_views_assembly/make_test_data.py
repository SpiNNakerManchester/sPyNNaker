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
from spynnaker.pyNN.utilities import neo_convertor
import pyNN.spiNNaker as sim

N_NEURONS = 9


def make_data(do_view):
    sim.setup(timestep=1.0)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

    pop_1 = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
    input = sim.Population(N_NEURONS, sim.SpikeSourceArray(
        spike_times=[[0, 10, 20],
                     [1, 21],
                     [2, 12, 22],
                     [3, 13, 23],
                     [14],
                     [5, 15, 25],
                     [],
                     [17, 27],
                     [8, 18, 28]]),
        label="input")
    sim.Projection(input, pop_1, sim.OneToOneConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    if do_view:
        # packets-per-timestep not allowed on a view
        pop_1[1, 2].record(["spikes", "v"])
    else:
        pop_1.record(["spikes", "v", "packets-per-timestep"])
    simtime = 35
    sim.run(simtime)

    if not do_view:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        neo = pop_1.get_data(
            variables=["spikes", "v",  "packets-per-timestep"])
        spikes = neo_convertor.convert_spikes(neo)
        print(spikes)
        my_spikes = os.path.join(my_dir, "spikes.csv")
        numpy.savetxt(my_spikes, spikes, delimiter=",")
        v = neo.segments[0].filter(name='v')[0]
        print(v)
        my_v = os.path.join(my_dir, "v.csv")
        numpy.savetxt(my_v, v, delimiter=",")
        packets = neo.segments[0].filter(name='packets-per-timestep')[0]
        print(packets)
        my_packets = os.path.join(my_dir, "packets-per-timestep.csv")
        numpy.savetxt(my_packets, packets, delimiter=",")
    sim.end()

    run_buffer = BaseDatabase.default_database_file()
    my_dir = os.path.dirname(os.path.abspath(__file__))
    if do_view:
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
    else:
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
    shutil.copyfile(run_buffer, my_buffer)


def make_rewires():
    sim.setup(1.0)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)
    stim = sim.Population(9, sim.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience elimination
    pop = sim.Population(9, sim.IF_curr_exp(), label="pop_1")

    # Elimination with random selection (0 probability formation)
    sim.Projection(
        stim, pop, sim.AllToAllConnector(),
        sim.StructuralMechanismStatic(
            partner_selection=sim.RandomSelection(),
            formation=sim.DistanceDependentFormation([3, 3], 0.0),
            elimination=sim.RandomByWeightElimination(4.0, 1.0, 1.0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=9, seed=0, weight=0.0, delay=1.0))

    pop.record("rewiring")

    sim.run(10)

    neo = pop.get_data("rewiring")
    elimination_events = neo.segments[0].events[1]

    num_elims = len(elimination_events.times)

    run_buffer = BaseDatabase.default_database_file()
    my_dir = os.path.dirname(os.path.abspath(__file__))
    my_labels = os.path.join(my_dir, "rewiring_labels.txt")

    with open(my_labels, "w", encoding="UTF-8") as label_f:
        for i in range(num_elims):
            label_f.write(elimination_events.labels[i])
            label_f.write("\n")

    sim.end()

    my_buffer = os.path.join(my_dir, "rewiring_data.sqlite3")
    shutil.copyfile(run_buffer, my_buffer)


if __name__ == '__main__':
    make_data(do_view=True)
    make_data(do_view=False)
    make_rewires()
