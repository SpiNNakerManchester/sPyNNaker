import pylab
import spynnaker.pyNN as sim

# -------------------------------------------------------------------
# This example uses the sPyNNaker implementation of the triplet rule
# Developed by Pfister and Gerstner(2006) to reproduce the pairing
# Experiment first performed by Sjostrom (2001)
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Common parameters
# -------------------------------------------------------------------
start_time = 100
time_between_pairs = 1000
num_pairs = 60

start_w = 0.5
frequencies = [0.1, 10, 20, 40, 50]
delta_t = [-10, 10]


def generate_fixed_frequency_test_data(frequency, first_spike_time,
                                       num_spikes):
    # Calculate interspike delays in ms
    interspike_delay = int(1000.0 / float(frequency));

    # Generate spikes
    return [first_spike_time + (s * interspike_delay)
            for s in range(num_spikes)]


# -------------------------------------------------------------------
# Experiment loop
# -------------------------------------------------------------------
# Population parameters
model = sim.IF_curr_exp
cell_params = {'cm': 0.25,        # nF
               'i_offset': 0.0,
               'tau_m': 10.0,
               'tau_refrac': 2.0,
               'tau_syn_E': 2.5,
               'tau_syn_I': 2.5,
               'v_reset': -70.0,
               'v_rest': -65.0,
               'v_thresh': -55.4}

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

# Sweep times and frequencies
projections = []
sim_time = 0
for t in delta_t:
    projections.append([])
    for f in frequencies:
        # Neuron populations
        pre_pop = sim.Population(1, model, cell_params)
        post_pop = sim.Population(1, model, cell_params)

        # Stimulating populations
        pre_times = generate_fixed_frequency_test_data(f, start_time - 1,
                                                       num_pairs + 1)
        post_times = generate_fixed_frequency_test_data(f, start_time + t,
                                                        num_pairs)
        pre_stim = sim.Population(1, sim.SpikeSourceArray,
                                  {'spike_times': [pre_times,]})
        post_stim = sim.Population(1, sim.SpikeSourceArray,
                                   {'spike_times': [post_times,]})

        # Update simulation time
        sim_time = max(sim_time, max(max(pre_times), max(post_times)) + 100)

        # Connections between spike sources and neuron populations
        ee_connector = sim.OneToOneConnector(weights=2)
        sim.Projection(pre_stim, pre_pop, ee_connector, target='excitatory')
        sim.Projection(post_stim, post_pop, ee_connector, target='excitatory')

        # **HACK**
        param_scale = 0.5

        # Plastic Connection between pre_pop and post_pop
        # Sjostrom visual cortex min-triplet params
        stdp_model = sim.STDPMechanism(
            timing_dependence=sim.PfisterSpikeTripletRule(
                tau_plus=16.8, tau_minus=33.7, tau_x=101, tau_y=114),
            weight_dependence=sim.AdditiveWeightDependence(
                w_min=0.0, w_max=1.0,
                A_plus=param_scale * 0.0,
                A_minus=param_scale * 7.1e-3,
                A3_plus=param_scale * 6.5e-3,
                A3_minus=param_scale * 0.0))

        projections[-1].append(sim.Projection(
            pre_pop, post_pop, sim.OneToOneConnector(weights=start_w),
            synapse_dynamics=sim.SynapseDynamics(slow=stdp_model)))

print("Simulating for %us" % (sim_time / 1000))

# Run simulation
sim.run(sim_time)

# Read weights from each parameter value being tested
weights = []
for projection_delta_t in projections:
    weights.append([p.getWeights()[0] for p in projection_delta_t])

# End simulation on SpiNNaker
sim.end(stop_on_board=True)

# -------------------------------------------------------------------
# Plotting
# -------------------------------------------------------------------
# Sjostrom et al. (2001) experimental data
data_w = [
    [-0.29, -0.41, -0.34, 0.56, 0.75],
    [-0.04, 0.14, 0.29, 0.53, 0.56]]
data_e = [
    [0.08, 0.11, 0.1, 0.32, 0.19],
    [0.05, 0.1, 0.14, 0.11, 0.26]]

# Plot Frequency response
figure, axis = pylab.subplots()
axis.set_xlabel("Frequency/Hz")
axis.set_ylabel(r"$(\frac{\Delta w_{ij}}{w_{ij}})$", rotation="horizontal",
                size="xx-large")

line_styles = ["--", "-"]
for m_w, d_w, d_e, l in zip(weights, data_w, data_e, line_styles):
    # Calculate deltas from end weights
    delta_w = [(w - start_w) / start_w for w in m_w]

    # Plot experimental data and error bars
    axis.errorbar(frequencies, d_w, yerr=d_e, color="black", linestyle=l,
                  label=r"Experimental data, delta $(\Delta{t}=%dms)$" % t)

    # Plot model data
    axis.plot(frequencies, delta_w, color="blue", linestyle=l,
              label=r"Triplet rule, delta $(\Delta{t}=%dms)$" % t)

axis.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0))

pylab.show()
