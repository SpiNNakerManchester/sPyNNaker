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
