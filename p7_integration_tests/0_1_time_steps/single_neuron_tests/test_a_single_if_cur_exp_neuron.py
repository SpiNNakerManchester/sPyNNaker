"""
test that a single neuron of if cur exp works as expected
"""

# general imports
import collections
import numpy
import pylab
import unittest
import spynnaker.pyNN as p

# Cell parameters
cell_params = {'cm': 0.25,
               'i_offset': 0.0,
               'tau_m': 20.0,
               'tau_refrac': 2.0,
               'tau_syn_E': 2.0,
               'tau_syn_I': 2.0,
               'v_reset': -60.0,
               'v_rest': -60.0,
               'v_thresh': -40.0}


class TestIfCurExpSingleNeuron(unittest.TestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    simtime = 4000
    noise_rate = 200

    def poisson_generator(self, rate, t_start, t_stop):
        """
        Generate poisson noise of given rate between start and stop times
        :param rate:
        :param t_start:
        :param t_stop:
        :return:
        """
        n = (t_stop - t_start) / 1000.0 * rate
        number = numpy.ceil(n + 3 * numpy.sqrt(n))
        if number < 100:
            number = min(5 + numpy.ceil(2 * n), 100)

        if number > 0:
            isi = numpy.random.exponential(1.0 / rate, number) * 1000.0
            if number > 1:
                spikes = numpy.add.accumulate(isi)
            else:
                spikes = isi
        else:
            spikes = numpy.array([])

        spikes += t_start
        i = numpy.searchsorted(spikes, t_stop)

        extra_spikes = []
        if len(spikes) == i:
            # ISI buf overrun

            t_last = (spikes[-1] +
                      numpy.random.exponential(1.0 / rate, 1)[0] * 1000.0)

            while t_last < t_stop:
                extra_spikes.append(t_last)
                t_last += numpy.random.exponential(1.0 / rate, 1)[0] * 1000.0

                spikes = numpy.concatenate((spikes, extra_spikes))
        else:
            spikes = numpy.resize(spikes, (i,))

        # Return spike times, rounded to millisecond boundaries
        return [round(x) for x in spikes]

    def simulate(self, spinnaker, input_spike_times):

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
        p.run(self.simtime)

        pop_voltages = pop.get_v(compatible_output=True)
        pop_spikes = pop.getSpikes(compatible_output=True)

        p.end()
        return pop_voltages, pop_spikes

    def plot_trace(self, trace, axis, label, colour):
        trace_unzipped = zip(*trace)
        axis.plot(trace_unzipped[1], trace_unzipped[2], color=colour,
                  label=label)

    def plot_noise(self, noise, axis, label, colour):
        axis.scatter(noise, [0] * len(noise), color=colour, label=label, s=4)

    def plot_raster(self, trace, axis, offset, label, colour):
        if trace is not None and len(trace) > 0:
            trace_unzipped = zip(*trace)
            trace_unzipped[0] = [t + offset for t in trace_unzipped[0]]
            axis.scatter(trace_unzipped[1], trace_unzipped[0],
                         color=colour, label=label, s=4)

    def test_single_neuron(self):
        # Generate poisson noise
        # **YUCK** remove duplicates as SpiNNaker implementation of spike
        # source array can only send one spike/neuron/ms
        noise_spike_times = self.poisson_generator(
            self.noise_rate, 0, self.simtime)
        noise_spike_times = list(
            collections.OrderedDict.fromkeys(noise_spike_times))

        # Simulate using both simulators
        s_pop_voltages, s_pop_spikes = self.simulate(
            True, noise_spike_times)
        n_pop_voltages, n_pop_spikes = self.simulate(
            False, noise_spike_times)

        _, axes = pylab.subplots(3, sharex=True)

        self.plot_noise(noise_spike_times, axes[0], "black", None)
        axes[0].set_title("Input spikes")
        axes[0].set_xlim((0, self.simtime))

        self.plot_raster(s_pop_spikes, axes[1], 0, "SpiNNaker", "red")
        self.plot_raster(n_pop_spikes, axes[1], 1, "NEST", "blue")
        axes[1].set_title("Output spikes")
        axes[1].set_xlim((0, self.simtime))

        numpy.save("spinnaker_voltages.npy", s_pop_voltages)
        numpy.save("nest_voltages.npy", n_pop_voltages)

        self.plot_trace(s_pop_voltages, axes[2], "SpiNNaker", "red")
        self.plot_trace(n_pop_voltages, axes[2], "NEST", "blue")
        axes[2].set_title("Membrane voltage")
        axes[2].set_ylabel("Voltage/mV")
        axes[2].set_ylim((-70, -35))
        axes[2].axhline(-40.0, linestyle="--")
        axes[2].legend()
        axes[2].set_xlim((0, self.simtime))

        pylab.show()
