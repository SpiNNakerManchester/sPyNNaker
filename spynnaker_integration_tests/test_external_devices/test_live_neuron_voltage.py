# Copyright (c) 2017 The University of Manchester
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

from collections import defaultdict
import decimal
from typing import Dict, List

import numpy
import pyNN.spiNNaker as p

from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utility_models import MultiCastCommand

from spynnaker.pyNN.external_devices_models import (
    AbstractEthernetTranslator, AbstractMulticastControllableDevice, SendType)
from spinnaker_testbase import BaseTestCase


class Translator(AbstractEthernetTranslator):

    def __init__(self, devices: List["Device"]):
        self.__keys = {device.device_control_key for device in devices}
        self.voltages: Dict[int, List[float]] = defaultdict(list)

    @overrides(AbstractEthernetTranslator.translate_control_packet)
    def translate_control_packet(
            self, multicast_packet: MultiCastCommand) -> None:
        if multicast_packet.key not in self.__keys:
            raise ValueError("Unknown key {} received".format(
                multicast_packet.key))
        voltage = multicast_packet.payload
        assert voltage is not None
        self.voltages[multicast_packet.key].append(
            (float)(decimal.Decimal(voltage) / DataType.S1615.scale))


class Device(AbstractMulticastControllableDevice):

    def __init__(self, key: int, time_betweeen_sending: int, partition: str):
        self.__key = key
        self.__time_between_sending = time_betweeen_sending
        self.__partition = partition

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_key)
    def device_control_key(self) -> int:
        return self.__key

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_max_value)
    def device_control_max_value(self) -> decimal.Decimal:
        return DataType.S1615.max

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_min_value)
    def device_control_min_value(self) -> float:
        return float(DataType.S1615.min)

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_partition_id)
    def device_control_partition_id(self) -> str:
        return self.__partition

    @property
    @overrides(AbstractMulticastControllableDevice.
               device_control_scaling_factor)
    def device_control_scaling_factor(self) -> int:
        return 1

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_send_type)
    def device_control_send_type(self) -> SendType:
        return SendType.SEND_TYPE_ACCUM

    @property
    @overrides(AbstractMulticastControllableDevice.
               device_control_timesteps_between_sending)
    def device_control_timesteps_between_sending(self) -> int:
        return self.__time_between_sending

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_uses_payload)
    def device_control_uses_payload(self) -> bool:
        return True


def spike_receiver(label: str, time: int, spikes: List[int]) -> None:
    print(f"Received spikes {spikes} from {label} at time {time}")


def live_neuron_voltage() -> None:
    p.setup(1.0)
    run_time = 1000.0
    create_edges = False
    time_1 = 10
    key_1 = 0x1
    devices_1 = [Device(key_1, time_1, "DEVICE_1")]
    translator_1 = Translator(devices_1)
    model_1 = p.external_devices.ExternalDeviceLifControl(
        devices_1, create_edges, translator_1)
    time_2_1 = 5
    key_2_1 = 0xE
    time_2_2 = 3
    key_2_2 = 0xF
    devices_2 = [Device(key_2_1, time_2_1, "DEVICE_1"),
                 Device(key_2_2, time_2_2, "DEVICE_2")]
    translator_2 = Translator(devices_2)
    model_2 = p.external_devices.ExternalDeviceLifControl(
        devices_2, create_edges, translator_2)
    conn = p.external_devices.SpynnakerLiveSpikesConnection(
        receive_labels=["stim"], local_port=None)
    conn.add_receive_callback("stim", spike_receiver)
    stim = p.Population(1, p.SpikeSourceArray(range(0, 1000, 100)),
                        label="stim")
    p.external_devices.activate_live_output_for(
        stim, database_notify_port_num=conn.local_port)
    ext_pop = p.external_devices.EthernetControlPopulation(
        len(devices_1), model_1)
    ext_pop.record(["v"])
    ext_pop_2 = p.external_devices.EthernetControlPopulation(
        len(devices_2), model_2)
    ext_pop_2.record(["v"])
    p.Projection(
        stim, ext_pop, p.OneToOneConnector(), p.StaticSynapse(1.0, 1.0))
    p.run(run_time)
    v = ext_pop.get_data("v").segments[0].analogsignals[0].as_array()[:, 0]
    p.end()
    relevant_v = v[1:1000:time_1]
    print(v)
    print(relevant_v)
    print(len(translator_1.voltages[key_1]), translator_1.voltages[key_1])
    print(len(translator_2.voltages[key_2_1]), translator_2.voltages[key_2_1])
    print(len(translator_2.voltages[key_2_2]), translator_2.voltages[key_2_2])
    assert len(translator_1.voltages[key_1]) >= (run_time // time_1) // 2
    assert len(translator_2.voltages[key_2_1]) >= (run_time // time_2_1) // 2
    assert len(translator_2.voltages[key_2_2]) >= (run_time // time_2_2) // 2
    assert numpy.sum(translator_2.voltages[key_2_1]) == 0
    assert numpy.sum(translator_2.voltages[key_2_2]) == 0

    # We can get packet loss so don't assume all voltages exist
    for volts in translator_1.voltages[key_1]:
        # We can reorder packets, so don't assume all packets are in order
        assert volts in relevant_v


class TestLiveNeuronVoltage(BaseTestCase):

    def test_live_neuron_voltage(self) -> None:
        self.runsafe(live_neuron_voltage)


if __name__ == '__main__':
    live_neuron_voltage()
