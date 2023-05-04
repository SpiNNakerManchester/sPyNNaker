import pyNN.spiNNaker as sim
from spinn_front_end_common.data.fec_data_view import FecDataView
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)


def test_possion_reset():
    """ Check that DSG still does the right thing after reset
    """
    sim.setup(1.0)
    noise = sim.Population(100, sim.SpikeSourcePoisson(
        rate=10.0), label="Noise")
    pop = sim.Population(100, sim.IF_curr_exp(), additional_parameters={
        "splitter": SplitterAbstractPopulationVertexNeuronsSynapses()})
    sim.Projection(noise, pop, sim.OneToOneConnector(), sim.StaticSynapse(1.0))

    sim.run(1000)
    sim.reset()
    # Force a data regeneration here to check Poisson is OK with this
    FecDataView.set_requires_data_generation()
    sim.run(1000)
    sim.end()
