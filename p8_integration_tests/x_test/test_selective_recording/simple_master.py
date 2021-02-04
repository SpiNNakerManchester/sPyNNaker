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

import os
import numpy
import spynnaker8 as sim

current_file_path = os.path.dirname(os.path.abspath(__file__))
spike_file = os.path.join(current_file_path, "master_spikes.csv")
v_file = os.path.join(current_file_path, "master_v.csv")
exc_file = os.path.join(current_file_path, "master_exc.csv")
inh_file = os.path.join(current_file_path, "master_inh.csv")

SIMTIME = 20000


def run_script():
    n_neurons = 500
    simtime = SIMTIME

    sim.setup(timestep=1)

    pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
    input1 = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                            label="input")
    sim.Projection(input1, pop_1, sim.AllToAllConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    input2 = sim.Population(n_neurons, sim.SpikeSourcePoisson(
        rate=100.0, seed=1), label="Stim_Exc")
    sim.Projection(input2, pop_1, sim.OneToOneConnector(),
                   synapse_type=sim.StaticSynapse(weight=5, delay=1))
    pop_1.record(['spikes', 'v', 'gsyn_exc', 'gsyn_inh'])
    sim.run(simtime)

    neo = pop_1.get_data()
    # pylint: disable=no-member
    spikes = neo.segments[0].spiketrains
    v = neo.segments[0].filter(name='v')[0]
    exc = neo.segments[0].filter(name='gsyn_exc')[0]
    inh = neo.segments[0].filter(name='gsyn_inh')[0]
    sim.end()

    return spikes, v,  exc, inh


def write_spikes(spikes):
    with open(spike_file, "w") as f:
        for i, spiketrain in enumerate(spikes):
            f.write("{}".format(i))
            for time in spiketrain.times:
                f.write(",{}".format(time.magnitude))
            f.write("\n")


if __name__ == '__main__':
    _spikes, _v, _exc, _inh = run_script()
    write_spikes(_spikes)
    numpy.savetxt(v_file, _v, delimiter=',')
    numpy.savetxt(exc_file, _exc, delimiter=',')
    numpy.savetxt(inh_file, _inh, delimiter=',')
