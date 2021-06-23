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
import random
from threading import Condition
import time
import spynnaker8 as Frontend
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase

# Create a condition to avoid overlapping prints
print_condition = Condition()


# Create an initialisation method
def init_pop(label, n_neurons, run_time_ms, machine_timestep_ms):
    print("{} has {} neurons".format(label, n_neurons))
    print("Simulation will run for {}ms at {}ms timesteps".format(
        run_time_ms, machine_timestep_ms))


# Create a sender of packets for the forward population
def send_input_forward(label, sender):
    for neuron_id in range(0, 100, 20):
        time.sleep(random.random() + 0.5)
        print_condition.acquire()
        print("Sending forward spike", neuron_id)
        print_condition.release()
        sender.send_spike(label, neuron_id, send_full_keys=True)


# Create a sender of packets for the backward population
def send_input_backward(label, sender):
    for neuron_id in range(0, 100, 20):
        real_id = 100 - neuron_id - 1
        time.sleep(random.random() + 0.5)
        print_condition.acquire()
        print("Sending backward spike", real_id)
        print_condition.release()
        sender.send_spike(label, real_id)


# Create a receiver of live spikes
def receive_spikes(label, time, neuron_ids):
    for neuron_id in neuron_ids:
        print_condition.acquire()
        print("Received spike at time", time, "from", label, "-", neuron_id)
        print_condition.release()


def do_run():

    # initial call to set up the front end (pynn requirement)
    Frontend.setup(timestep=1.0, min_delay=1.0)

    # neurons per population and the length of runtime in ms for the
    # simulation, as well as the expected weight each spike will contain
    n_neurons = 100
    run_time = 8000
    weight_to_spike = 2.0

    # neural parameters of the ifcur model used to respond to injected spikes.
    # (cell params for a synfire chain)
    cell_params_lif = {'cm': 0.25,
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0
                       }

    ##################################
    # Parameters for the injector population.  This is the minimal set of
    # parameters required, which is for a set of spikes where the key is not
    # important.  Note that a virtual key *will* be assigned to the population,
    # and that spikes sent which do not match this virtual key will be dropped;
    # however, if spikes are sent using 16-bit keys, they will automatically be
    # made to match the virtual key.  The virtual key assigned can be obtained
    # from the database.
    ##################################
    cell_params_spike_injector = {

        # The port on which the spiNNaker machine should listen for packets.
        # Packets to be injected should be sent to this port on the spiNNaker
        # machine
        'port': 12345,
    }

    ##################################
    # Parameters for the injector population.  Note that each injector needs to
    # be given a different port.  The virtual key is assigned here, rather than
    # being allocated later.  As with the above, spikes injected need to match
    # this key, and this will be done automatically with 16-bit keys.
    ##################################
    cell_params_spike_injector_with_key = {

        # The port on which the spiNNaker machine should listen for packets.
        # Packets to be injected should be sent to this port on the spiNNaker
        # machine
        'port': 12346,

        # This is the base key to be used for the injection, which is used to
        # allow the keys to be routed around the spiNNaker machine.  This
        # assignment means that 32-bit keys must have the high-order 16-bit
        # set to 0x7; This will automatically be prepended to 16-bit keys.
        'virtual_key': 0x70000,
    }

    # create synfire populations (if cur exp)
    pop_forward = Frontend.Population(n_neurons,
                                      Frontend.IF_curr_exp(**cell_params_lif),
                                      label='pop_forward')
    pop_backward = Frontend.Population(n_neurons,
                                       Frontend.IF_curr_exp(**cell_params_lif),
                                       label='pop_backward')

    # Create injection populations
    injector_forward = Frontend.Population(
        n_neurons,
        Frontend.external_devices.SpikeInjector(),
        additional_parameters=cell_params_spike_injector_with_key,
        label='spike_injector_forward')
    injector_backward = Frontend.Population(
        n_neurons, Frontend.external_devices.SpikeInjector(),
        additional_parameters=cell_params_spike_injector,
        label='spike_injector_backward')

    # Create a connection from the injector into the populations
    Frontend.Projection(injector_forward, pop_forward,
                        Frontend.OneToOneConnector(),
                        Frontend.StaticSynapse(weight=weight_to_spike))
    Frontend.Projection(injector_backward, pop_backward,
                        Frontend.OneToOneConnector(),
                        Frontend.StaticSynapse(weight=weight_to_spike))

    # Synfire chain connection where each neuron is connected to next neuron
    # NOTE: there is no recurrent connection so that each chain stops once it
    # reaches the end
    loop_forward = list()
    loop_backward = list()
    for i in range(0, n_neurons - 1):
        loop_forward.append((i, (i + 1) % n_neurons, weight_to_spike, 3))
        loop_backward.append(((i + 1) % n_neurons, i, weight_to_spike, 3))
    Frontend.Projection(pop_forward, pop_forward,
                        Frontend.FromListConnector(loop_forward),
                        Frontend.StaticSynapse(weight=weight_to_spike,
                                               delay=3))
    Frontend.Projection(pop_backward, pop_backward,
                        Frontend.FromListConnector(loop_backward),
                        Frontend.StaticSynapse(weight=weight_to_spike,
                                               delay=3))

    # record spikes from the synfire chains so that we can read off valid
    # results in a safe way afterwards, and verify the behaviour
    pop_forward.record(['spikes'])
    pop_backward.record(['spikes'])

    # Activate the sending of live spikes
    Frontend.external_devices.activate_live_output_for(pop_forward)
    Frontend.external_devices.activate_live_output_for(pop_backward)

    # Set up the live connection for sending spikes
    live_spikes_connection_send = \
        Frontend.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=None, local_port=None,
            send_labels=["spike_injector_forward", "spike_injector_backward"])
    Frontend.external_devices.add_database_socket_address(
        live_spikes_connection_send.local_ip_address,
        live_spikes_connection_send.local_port, None)

    # Set up callbacks to occur at initialisation
    live_spikes_connection_send.add_init_callback(
        "spike_injector_forward", init_pop)
    live_spikes_connection_send.add_init_callback(
        "spike_injector_backward", init_pop)

    # Set up callbacks to occur at the start of simulation
    live_spikes_connection_send.add_start_resume_callback(
        "spike_injector_forward", send_input_forward)
    live_spikes_connection_send.add_start_resume_callback(
        "spike_injector_backward", send_input_backward)

    # if not using the c visualiser, then a new spynnaker live spikes
    # connection is created to define that there is a python function which
    # receives the spikes.
    live_spikes_connection_receive = \
        Frontend.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=["pop_forward", "pop_backward"],
            local_port=None, send_labels=None)
    Frontend.external_devices.add_database_socket_address(
        live_spikes_connection_receive.local_ip_address,
        live_spikes_connection_receive.local_port, None)

    # Set up callbacks to occur when spikes are received
    live_spikes_connection_receive.add_receive_callback(
        "pop_forward", receive_spikes)
    live_spikes_connection_receive.add_receive_callback(
        "pop_backward", receive_spikes)

    # Run the simulation on spiNNaker
    Frontend.run(run_time)
    Frontend.run(run_time)

    # Retrieve spikes from the synfire chain population
    spikes_forward = neo_convertor.convert_spikes(
        pop_forward.get_data('spikes'))
    spikes_backward = neo_convertor.convert_spikes(
        pop_backward.get_data('spikes'))

    # Clear data structures on spiNNaker to leave the machine in a clean state
    # for future executions
    Frontend.end()

    return (spikes_forward, spikes_backward)


class SpikeIoMultiRun(BaseTestCase):

    def check_run(self):
        (spikes_forward, spikes_backward) = do_run()
        self.assertEqual(600, len(spikes_forward))
        self.assertEqual(600, len(spikes_backward))

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    import pylab

    (spikes_forward, spikes_backward) = do_run()
    print(len(spikes_forward))
    print(len(spikes_backward))

    # If there are spikes, plot using matplotlib
    if len(spikes_forward) != 0 or len(spikes_backward) != 0:
        pylab.figure()
        if len(spikes_forward) != 0:
            pylab.plot([i[1] for i in spikes_forward],
                       [i[0] for i in spikes_forward], "b.")
        if len(spikes_backward) != 0:
            pylab.plot([i[1] for i in spikes_backward],
                       [i[0] for i in spikes_backward], "r.")
        pylab.ylabel('neuron id')
        pylab.xlabel('Time/ms')
        pylab.title('spikes')
        pylab.show()
    else:
        print("No spikes received")
