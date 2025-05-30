# Copyright (c) 2021 The University of Manchester
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

import traceback
from time import sleep
from typing import List

import pyNN.spiNNaker as p

from spinn_utilities.exceptions import SimulatorShutdownException

from spinn_front_end_common.utilities.connections import LiveEventConnection

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.external_devices import SpynnakerLiveSpikesConnection

sim_finished = False
n_spikes = list()
n_spikes.append(0)


def recv(label: str, time: int, neuron_ids: List[int]) -> None:
    """ Receive spikes and add the number received to the current segment count
    """
    print("Time: {}; Received spikes from {}:{}".format(
        time, label, neuron_ids))
    n_spikes[len(n_spikes) - 1] += len(neuron_ids)


def send_sync(label: str, conn: LiveEventConnection) -> None:
    """ Send "continue" signal after a delay and update the current segment
    """
    global sim_finished
    while not sim_finished:
        sleep(0.1)
        if not sim_finished:
            print("Sending sync")
            try:
                n_spikes.append(0)
                p.external_devices.continue_simulation()
            except SimulatorShutdownException:
                # Weird raise condition lost
                sim_finished = True
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()


def stop(label: str, conn: LiveEventConnection) -> None:
    """ Mark the simulation finished to stop sending the sync signal
    """
    global sim_finished
    sim_finished = True


def test_live_sync() -> None:
    """ Test the synchronisation from host behaviour by receiving live spikes
        and checking that the right spikes only arrive after synchronisation
    """
    global sim_finished
    global n_spikes
    conn = SpynnakerLiveSpikesConnection(
        receive_labels=["ssa"], local_port=None)
    conn.add_receive_callback("ssa", recv)
    conn.add_start_resume_callback("ssa", send_sync)
    conn.add_pause_stop_callback("ssa", stop)

    p.setup(1.0)
    pop = p.Population(
        100, p.SpikeSourceArray([[i] for i in range(100)]), label="ssa")
    p.external_devices.activate_live_output_for(
        pop, database_notify_port_num=conn.local_port)

    try:
        p.external_devices.run_sync(100, 20)
    except Exception:
        if sim_finished:
            SpynnakerDataView.raise_skiptest("Stopped too soon")

    sim_finished = True
    p.end()

    # On slow connections send_sync is sent more often
    n_spikes = [x for x in n_spikes if x > 0]
    assert 5 == len(n_spikes)

    # 20 spikes should be in each range, but some could get lost, so check
    # for a range
    for i in range(5):
        assert n_spikes[i] >= 10 and n_spikes[i] <= 20
