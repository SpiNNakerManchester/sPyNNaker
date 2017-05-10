"""
test that a single neuron of if cur exp works as expected
"""

# general imports
import numpy
import unittest

from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.pyNN as p

from p7_integration_tests.scripts.synfire_run import TestRun
from spynnaker.pyNN import SpikeSourcePoisson

cell_params = {'cm': 0.25,
               'i_offset': 0.0,
               'tau_m': 20.0,
               'tau_refrac': 2.0,
               'tau_syn_E': 2.0,
               'tau_syn_I': 2.0,
               'v_reset': -60.0,
               'v_rest': -60.0,
               'v_thresh': -40.0}

simtime = 4000
noise_rate = 200
synfire_run = TestRun()


# currently dead code but new way is broken
def simulate(input_spike_times):

    rng = p.NumpyRNG(seed=28375)
    v_init = p.RandomDistribution('uniform', [-60, -40], rng)

    p.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

    pop = p.Population(1, p.IF_curr_exp, cell_params, label='population')
    pop.randomInit(v_init)
    pop.record()
    pop.record_v()

    noise = p.Population(1, p.SpikeSourceArray,
                         {"spike_times": input_spike_times})

    p.Projection(noise, pop, p.OneToOneConnector(weights=0.4, delays=1),
                 target='excitatory')

    # Simulate
    p.run(simtime)

    pop_voltages = pop.get_v(compatible_output=True)
    pop_spikes = pop.getSpikes(compatible_output=True)

    p.end()
    return pop_voltages, pop_spikes


def plot_trace(trace, axis, label, colour):
    trace_unzipped = zip(*trace)
    axis.plot(trace_unzipped[1], trace_unzipped[2], color=colour,
              label=label)


def plot_noise(noise, axis, label, colour):
    axis.scatter(noise, [0] * len(noise), color=colour, label=label, s=4)


def plot_raster(trace, axis, offset, label, colour):
    if trace is not None and len(trace) > 0:
        trace_unzipped = zip(*trace)
        trace_unzipped[0] = [t + offset for t in trace_unzipped[0]]
        axis.scatter(trace_unzipped[1], trace_unzipped[0],
                     color=colour, label=label, s=4)


def do_run():

    # Simulate using both simulators
    synfire_run.do_run(
        n_neurons=1, input_class=SpikeSourcePoisson, rate=noise_rate,
        start_time=0, duration=simtime, use_loop_connections=False,
        cell_params=cell_params, run_times=[simtime], record=True,
        record_v=True, randomise_v_init=True, record_input_spikes=True,
        weight_to_spike=0.4)

    s_pop_voltages = synfire_run.get_output_pop_voltage()
    s_pop_spikes = synfire_run.get_output_pop_spikes()
    noise_spike_times = synfire_run.get_spike_source_spikes()

    return noise_spike_times, s_pop_spikes, s_pop_voltages


def plot(noise_spike_times, s_pop_spikes, s_pop_voltages):
    import pylab  # deferred so unittest are not dependent on it

    _, axes = pylab.subplots(3, sharex=True)

    plot_noise(noise_spike_times, axes[0], "black", None)
    axes[0].set_title("Input spikes")
    axes[0].set_xlim((0, simtime))

    plot_raster(s_pop_spikes, axes[1], 0, "SpiNNaker", "red")
    axes[1].set_title("Output spikes")
    axes[1].set_xlim((0, simtime))

    numpy.save("spinnaker_voltages.npy", s_pop_voltages)

    plot_trace(s_pop_voltages, axes[2], "SpiNNaker", "red")
    axes[2].set_title("Membrane voltage")
    axes[2].set_ylabel("Voltage/mV")
    axes[2].set_ylim((-70, -35))
    axes[2].axhline(-40.0, linestyle="--")
    axes[2].legend()
    axes[2].set_xlim((0, simtime))

    pylab.show()


class TestIfCurExpSingleNeuron(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    # TODO Alan to check why now broken!
    @unittest.skip("skipping p7_integration_tests/"
                   "0_1_time_steps/single_neuron_tests/"
                   "test_a_single_if_cur_exp_neuron.py")
    def test_single_neuron(self):
        results = do_run()
        (noise_spike_times, s_pop_spikes, s_pop_voltages) = results
        self.assertLess(2, len(s_pop_spikes))
        self.assertGreater(15, len(s_pop_spikes))


if __name__ == '__main__':
    results = do_run()
    (noise_spike_times, s_pop_spikes,  s_pop_voltages) = results
    print len(s_pop_spikes)
    plot(noise_spike_times, s_pop_spikes, s_pop_voltages)
