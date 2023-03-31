# Copyright (c) 2023 The University of Manchester
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

import pyNN.spiNNaker as p
import pytest


def test_spif_io():
    p.setup(1.0)
    spif_input = p.Population(
        None, p.external_devices.SPIFRetinaDevice(0, 640, 480, 32, 16),
        label="input")
    spif_output = p.Population(
        None, p.external_devices.SPIFOutputDevice(create_database=True),
        label="output")
    another_population = p.Population(
        100, p.SpikeSourcePoisson(rate=10), label="poisson")

    p.external_devices.activate_live_output_to(spif_input, spif_output)
    p.external_devices.activate_live_output_to(another_population, spif_output)

    p.run(1000)
    p.end()


def test_spif_errors():
    p.setup(1.0)
    spif_output = p.Population(
        None, p.external_devices.SPIFOutputDevice(create_database=False))

    # Wrong splitting
    with pytest.raises(ValueError):
        p.set_number_of_neurons_per_core(p.IF_curr_exp, 50)
        pop = p.Population(100, p.IF_curr_exp())
        p.external_devices.activate_live_output_to(pop, spif_output)

    # Just enough
    for _ in range(6):
        pop = p.Population(100, p.SpikeSourcePoisson(rate=10))
        p.external_devices.activate_live_output_to(pop, spif_output)

    # One too many
    with pytest.raises(ValueError):
        pop = p.Population(100, p.SpikeSourcePoisson(rate=10))
        p.external_devices.activate_live_output_to(pop, spif_output)

    p.end()
