# Copyright (c) 2017-2022 The University of Manchester
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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase

# Parameters:
simulationParameters = {"simTime": 10, "timeStep": 1.0}
popNeurons = {"ILayer": 2, "LIFLayer": 2}
ILSpike = [[1, 6, 11, 16, 21], []]
neuronParameters = {
    "LIFL": {"cm": 0.27, "i_offset": 0.0, "tau_m": 10.0, "tau_refrac": 1.0,
             "tau_syn_E": 0.3, "tau_syn_I": 0.3, "v_reset": -60.0,
             "v_rest": -60.0, "v_thresh": -55.0}
}
initNeuronParameters = {
    "LIFL": {"vInit": -60}
}
synParameters = {
    "LIFL-LIFL": {"tau_plus": 5.0, "tau_minus": 5.0, "A_plus": 0.1,
                  "A_minus": 0.1, "w_max": 10.0, "w_min": 1.0,
                  "initWeight": 5.0, "delay": 1.0, "receptor_type": "STDP"},
    "IL-LIFL": {"initWeight": 5.0, "delay": 1.0, "receptor_type": "excitatory"}
}


# Network and simulation
def record_weights_using_callback():

    ######################################
    # Setup
    ######################################
    sim.setup(timestep=simulationParameters["timeStep"])

    ######################################
    # Neuron pop
    ######################################
    # Input neurons
    ILayer = sim.Population(
        popNeurons["ILayer"], sim.SpikeSourceArray(spike_times=ILSpike),
        label="ILayer")
    # LIF neurons
    LIFLayer = sim.Population(
        popNeurons["LIFLayer"], sim.IF_curr_exp(**neuronParameters["LIFL"]),
        label="LIFLayer")
    LIFLayer.initialize(v=initNeuronParameters["LIFL"]["vInit"])

    ######################################
    # Synapses
    ######################################

    # ILayer-LIFLayer -> statics
    sim.Projection(
        ILayer, LIFLayer, sim.OneToOneConnector(),
        synapse_type=sim.StaticSynapse(
            weight=synParameters["IL-LIFL"]["initWeight"],
            delay=synParameters["IL-LIFL"]["delay"]))

    # LIFLayer-ILayer -> STDP
    timing_rule = sim.SpikePairRule(
        tau_plus=synParameters["LIFL-LIFL"]["tau_plus"],
        tau_minus=synParameters["LIFL-LIFL"]["tau_minus"],
        A_plus=synParameters["LIFL-LIFL"]["A_plus"],
        A_minus=synParameters["LIFL-LIFL"]["A_minus"])
    weight_rule = sim.AdditiveWeightDependence(
        w_max=synParameters["LIFL-LIFL"]["w_max"],
        w_min=synParameters["LIFL-LIFL"]["w_min"])
    stdp_model = sim.STDPMechanism(
        timing_dependence=timing_rule, weight_dependence=weight_rule,
        weight=synParameters["LIFL-LIFL"]["initWeight"],
        delay=synParameters["LIFL-LIFL"]["delay"])
    LIFLayer_LIFLayer_conn = sim.Projection(
        LIFLayer, LIFLayer,
        sim.AllToAllConnector(allow_self_connections=False),
        synapse_type=stdp_model)

    ######################################
    # Record parameters
    ######################################
    LIFLayer.record(["spikes", "v"])
    weightRecorderLIF_LIF = weight_recorder(
        sampling_interval=simulationParameters["timeStep"],
        projection=LIFLayer_LIFLayer_conn)

    ######################################
    # Run simulation
    ######################################
    sim.run(simulationParameters["simTime"], callbacks=[weightRecorderLIF_LIF])

    ######################################
    # Recall data
    ######################################
    populationData = LIFLayer.get_data(variables=["spikes", "v"])
    LIFLSpikes = populationData.segments[0].spiketrains
    vLIFL = populationData.segments[0].filter(name='v')[0]
    w_LIFL_LIFL = weightRecorderLIF_LIF.get_weights()

    ######################################
    # End simulation
    ######################################
    sim.end()

    ######################################
    # Return parameters
    ######################################
    return ILSpike, LIFLSpikes, vLIFL, w_LIFL_LIFL


# http://neuralensemble.org/docs/PyNN/examples/simple_STDP.html
class weight_recorder(object):
    """
    Recording of weights is not yet built in to PyNN, so therefore we need
    to construct a callback object, which reads the current weights from
    the projection at regular intervals.
    """

    def __init__(self, sampling_interval, projection):
        self.interval = sampling_interval
        self.projection = projection
        self._weights = []

    def __call__(self, t):
        self._weights.append(
            self.projection.get('weight', format='list', with_address=True))
        return t + self.interval

    def get_weights(self):
        return self._weights


# Network and simulation
def record_weights_using_multirun():

    ######################################
    # Setup
    ######################################
    sim.setup(timestep=simulationParameters["timeStep"])

    ######################################
    # Neuron pop
    ######################################
    # Input neurons
    ILayer = sim.Population(
        popNeurons["ILayer"], sim.SpikeSourceArray(spike_times=ILSpike),
        label="ILayer")
    # LIF neurons
    LIFLayer = sim.Population(
        popNeurons["LIFLayer"], sim.IF_curr_exp(**neuronParameters["LIFL"]),
        label="LIFLayer")
    LIFLayer.initialize(v=initNeuronParameters["LIFL"]["vInit"])

    ######################################
    # Synapses
    ######################################

    # ILayer-LIFLayer -> statics
    sim.Projection(
        ILayer, LIFLayer, sim.OneToOneConnector(),
        synapse_type=sim.StaticSynapse(
            weight=synParameters["IL-LIFL"]["initWeight"],
            delay=synParameters["IL-LIFL"]["delay"]))

    # LIFLayer-ILayer -> STDP
    timing_rule = sim.SpikePairRule(
        tau_plus=synParameters["LIFL-LIFL"]["tau_plus"],
        tau_minus=synParameters["LIFL-LIFL"]["tau_minus"],
        A_plus=synParameters["LIFL-LIFL"]["A_plus"],
        A_minus=synParameters["LIFL-LIFL"]["A_minus"])
    weight_rule = sim.AdditiveWeightDependence(
        w_max=synParameters["LIFL-LIFL"]["w_max"],
        w_min=synParameters["LIFL-LIFL"]["w_min"])
    stdp_model = sim.STDPMechanism(
        timing_dependence=timing_rule, weight_dependence=weight_rule,
        weight=synParameters["LIFL-LIFL"]["initWeight"],
        delay=synParameters["LIFL-LIFL"]["delay"])
    LIFLayer_LIFLayer_conn = sim.Projection(
        LIFLayer, LIFLayer,
        sim.AllToAllConnector(allow_self_connections=False),
        synapse_type=stdp_model)

    ######################################
    # Record parameters
    ######################################
    LIFLayer.record(["spikes", "v"])

    ######################################
    # Run simulation
    ######################################
    w_LIFL_LIFL = []
    w_LIFL_LIFL.append(LIFLayer_LIFLayer_conn.get(["weight"], "list"))
    for n in range(simulationParameters["simTime"]):
        sim.run(1)
        w_LIFL_LIFL.append(LIFLayer_LIFLayer_conn.get(["weight"], "list"))

    ######################################
    # Recall data
    ######################################
    populationData = LIFLayer.get_data(variables=["spikes", "v"])
    LIFLSpikes = populationData.segments[0].spiketrains
    vLIFL = populationData.segments[0].filter(name='v')[0]

    ######################################
    # End simulation
    ######################################
    sim.end()

    ######################################
    # Return parameters
    ######################################
    return ILSpike, LIFLSpikes, vLIFL, w_LIFL_LIFL


class TestSTDPRecordWeights(BaseTestCase):
    def do_run(self):
        ILSpike_c, LIFLS_c, v_c, w_callback = record_weights_using_callback()

        ILSpike_r, LIFLS_r, v_r, w_multirun = record_weights_using_multirun()

        assert all(wc[0] == wm[0] for wc, wm in zip(w_callback, w_multirun))
        assert all(wc[1] == wm[1] for wc, wm in zip(w_callback, w_multirun))

    def test_STDP_record_weights(self):
        self.runsafe(self.do_run)


if __name__ == "__main__":
    ILSpike, LIFLSpikes, vLIFL, w_callback = record_weights_using_callback()
    ILSpike, LIFLSpikes, vLIFL, w_multirun = record_weights_using_multirun()
    print(ILSpike)
    print(LIFLSpikes)
    print(vLIFL)
    print(w_callback)
    print(w_multirun)
