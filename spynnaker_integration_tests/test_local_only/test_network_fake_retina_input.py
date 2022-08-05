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
from pyNN.space import Grid2D
from random import randint
from spinnaker_testbase import BaseTestCase

# Used if send_fake_spikes is True
sleep_time = 0.1
n_packets = 20

run_time = (n_packets + 1) * sleep_time * 1000

# Constants
WIDTH = 8  # 640
HEIGHT = int(WIDTH * 3/4)  # 480
# Creates 512 neurons per core
SUB_WIDTH = 32
SUB_HEIGHT = 16
# Weight of connections between "layers"
WEIGHT = 5


def get_retina_input():
    """ This is used to create random input as a spike array
    """

    time = int(sleep_time * 1000)
    spikes_to_send = [[] for _ in range(WIDTH * HEIGHT)]
    for _ in range(n_packets):
        n_spikes = randint(10, 100)
        for _ in range(n_spikes):
            x = randint(0, WIDTH - 1)
            y = randint(0, HEIGHT - 1)
            packed_coord = (y * WIDTH) + x
            spikes_to_send[packed_coord].append(time)
            print(f"Sending x={x}, y={y}, packed={hex(packed_coord)}")
            time += (sleep_time * 1000)
    return spikes_to_send


def find_next_spike_after(spike_times, time):
    for index, spike_time in enumerate(spike_times):
        if spike_time >= time:
            return index, spike_time
    return None, None


def find_square_of_spikes(x, y, time, spikes, s_label, t_label):
    found_spikes = list()
    last_target_time = None
    for x_t in range(x - 1, x + 2):
        if x_t < 0 or x_t >= WIDTH:
            continue
        for y_t in range(y - 1, y + 2):
            if y_t < 0 or y_t >= HEIGHT:
                continue
            target_neuron = (y_t * WIDTH) + x_t
            index, target_time = find_next_spike_after(
                spikes[target_neuron], time)
            if index is None:
                raise Exception(
                    f"Spike in source {s_label}: {x}, {y} at time {time} not"
                    f" found in target {t_label}: {x_t}, {y_t}:"
                    f" {spikes[target_neuron]}")
            if last_target_time is not None:
                if last_target_time != target_time:
                    raise Exception(
                        f"Spike in source {s_label}: {x}, {y} at time {time}"
                        " does not have matching time in all surrounding"
                        " targets")
            found_spikes.append((x_t, y_t, target_time))
            # print(f"Spike in source {s_label}: {x}, {y} at time {time} matches"
            #       f" target {t_label}: {x_t}, {y_t} at time {target_time}")
    return spikes, found_spikes


def do_run():
    # Set up PyNN
    p.setup(1.0)

    # Set the number of neurons per core to a rectangle
    # (creates 512 neurons per core)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, (SUB_WIDTH, SUB_HEIGHT))
    # (creates 2048 sources per core)
    p.set_number_of_neurons_per_core(p.SpikeSourceArray,
                                     ((SUB_WIDTH * 2), (SUB_HEIGHT * 2)))

    # This is our convolution connector.  This one doesn't do much!
    conn = p.ConvolutionConnector([[WEIGHT, WEIGHT, WEIGHT],
                                   [WEIGHT, WEIGHT, WEIGHT],
                                   [WEIGHT, WEIGHT, WEIGHT]], padding=(1, 1))

    capture_conn = p.ConvolutionConnector([[WEIGHT]])

    # This is a fake retina
    dev = p.Population(
        WIDTH * HEIGHT, p.SpikeSourceArray(get_retina_input()),
        structure=Grid2D(WIDTH / HEIGHT), label="Spike Source")

    # Create a population that captures the spikes from the input
    capture = p.Population(
        WIDTH * HEIGHT, p.IF_curr_exp(), structure=Grid2D(WIDTH / HEIGHT),
        label="Capture")
    p.Projection(dev, capture, capture_conn, p.Convolution())

    # Create some convolutional "layers" (just 2, with 1 convolution each here)
    pop = p.Population(
        WIDTH * HEIGHT, p.IF_curr_exp(), structure=Grid2D(WIDTH / HEIGHT),
        label="Layer One")
    pop_2 = p.Population(
        WIDTH * HEIGHT, p.IF_curr_exp(), structure=Grid2D(WIDTH / HEIGHT),
        label="Layer Two")

    # Record the spikes so we know what happened
    capture.record("spikes")
    pop.record("spikes")
    pop_2.record("spikes")

    # Create convolution connections from the device -> first pop -> second pop
    # These use the same connector, but could be different if desired
    p.Projection(dev, pop, conn, p.Convolution())
    p.Projection(pop, pop_2, conn, p.Convolution())

    # Run the simulation for long enough for packets to be sent
    p.run(run_time)

    # Get out the spikes
    capture_spikes = capture.get_data("spikes").segments[0].spiketrains
    layer_1_spikes = pop.get_data("spikes").segments[0].spiketrains
    layer_2_spikes = pop_2.get_data("spikes").segments[0].spiketrains

    # Tell the software we are done with the board
    p.end()

    return (capture_spikes, layer_1_spikes, layer_2_spikes)


class SingleSpikeKernelResponse(BaseTestCase):

    def check_run(self):
        (capture_spikes, layer_1_spikes, layer_2_spikes) = do_run()
        # Print what happened
        for neuron_id in range(len(capture_spikes)):
            # Work out x and y of neuron
            x = neuron_id % WIDTH
            y = neuron_id // WIDTH

            if (len(capture_spikes[neuron_id]) > 0 or
                    len(layer_1_spikes[neuron_id]) > 0 or
                    len(layer_2_spikes[neuron_id]) > 0):
                print(f"{x}, {y}: {capture_spikes[neuron_id]}, "
                      f"{layer_1_spikes[neuron_id]}, "
                      f"{layer_2_spikes[neuron_id]}")

        # Check what happened
        for neuron_id in range(len(capture_spikes)):
            # Work out x and y of neuron
            x = neuron_id % WIDTH
            y = neuron_id // WIDTH

            # Go through the spikes one by one and check they match up
            for spike_time in capture_spikes[neuron_id]:
                layer_1_spikes, found_times = find_square_of_spikes(
                    x, y, spike_time, layer_1_spikes, "device", "layer 1")

                # Check that the next layer matches as well
                for x_1, y_1, time_1 in found_times:
                    layer_2_spikes, _ = find_square_of_spikes(
                        x_1, y_1, time_1, layer_2_spikes, "layer 1", "layer 2")

        # TODO convert this into something that can be asserted or checked?
        print("Passed!")

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    (capture_spikes, layer_1_spikes, layer_2_spikes) = do_run()
    # Print what happened
    for neuron_id in range(len(capture_spikes)):
        # Work out x and y of neuron
        x = neuron_id % WIDTH
        y = neuron_id // WIDTH

        if (len(capture_spikes[neuron_id]) > 0 or
                len(layer_1_spikes[neuron_id]) > 0 or
                len(layer_2_spikes[neuron_id]) > 0):
            print(f"{x}, {y}: {capture_spikes[neuron_id]}, "
                  f"{layer_1_spikes[neuron_id]}, "
                  f"{layer_2_spikes[neuron_id]}")

    # Check what happened
    for neuron_id in range(len(capture_spikes)):
        # Work out x and y of neuron
        x = neuron_id % WIDTH
        y = neuron_id // WIDTH

        # Go through the spikes one by one and check they match up
        for spike_time in capture_spikes[neuron_id]:
            layer_1_spikes, found_times = find_square_of_spikes(
                x, y, spike_time, layer_1_spikes, "device", "layer 1")

            # Check that the next layer matches as well
            for x_1, y_1, time_1 in found_times:
                layer_2_spikes, _ = find_square_of_spikes(
                    x_1, y_1, time_1, layer_2_spikes, "layer 1", "layer 2")
    print("Passed!")
