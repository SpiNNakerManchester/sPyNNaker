import spynnaker.pyNN as pynn
import numpy as np
from pyNN.random import NumpyRNG, RandomDistribution

simulator_Name = 'spiNNaker'


def poisson_generator(rate, rng, t_start=0.0, t_stop=1000.0, array=True,
                      debug=False):
    """
    Returns a SpikeTrain whose spikes are a realization of a Poisson process
    with the given rate (Hz) and stopping time t_stop (milliseconds).

    Note: t_start is always 0.0, thus all realizations are as if
    they spiked at t=0.0, though this spike is not included in the SpikeList.

    Inputs:
        rate    - the rate of the discharge (in Hz)
        t_start - the beginning of the SpikeTrain (in ms)
        t_stop  - the end of the SpikeTrain (in ms)
        array   - if True, a numpy array of sorted spikes is returned,
                  rather than a SpikeTrain object.

    Examples:
        >> gen.poisson_generator(50, 0, 1000)
        >> gen.poisson_generator(20, 5000, 10000, array=True)

    See also:
        inh_poisson_generator, inh_gamma_generator,
        inh_adaptingmarkov_generator
    """

    n = (t_stop - t_start) / 1000.0 * rate
    number = np.ceil(n + 3 * np.sqrt(n))
    if number < 100:
        number = min(5 + np.ceil(2 * n), 100)

    if number > 0:
        isi = rng.exponential(1.0 / rate, number) * 1000.0
        if number > 1:
            spikes = np.add.accumulate(isi)
        else:
            spikes = isi
    else:
        spikes = np.array([])

    spikes += t_start
    i = np.searchsorted(spikes, t_stop)

    extra_spikes = []
    if i == len(spikes):
        # ISI buf overrun

        t_last = spikes[-1] + rng.exponential(1.0 / rate, 1)[0] * 1000.0

        while (t_last < t_stop):
            extra_spikes.append(t_last)
            t_last += rng.exponential(1.0 / rate, 1)[0] * 1000.0

        spikes = np.concatenate((spikes, extra_spikes))

        if debug:
            print("ISI buf overrun handled. len(spikes)=%d,"
                  " len(extra_spikes)=%d" % (len(spikes), len(extra_spikes)))

    else:
        spikes = np.resize(spikes, (i,))

    if debug:
        return spikes, extra_spikes
    else:
        return [round(x) for x in spikes]


def do_run(Neurons, sim_time, record):
    """

    :param Neurons: Number of Neurons
    :type Neurons: int
    :param sim_time: times for run
    :type sim_time: int
    :param record: If True will aks for spikes to be recorded
    :type record: bool
    """
    g = 5.0
    eta = 2.0
    delay = 2.0
    epsilon = 0.1

    tau_m = 20.0  # ms (20ms will give a FR of 20hz)
    tau_ref = 2.0
    v_reset = 10.0
    V_th = 20.0
    v_rest = 0.0
    tauSyn = 1.0

    N_E = int(round(Neurons * 0.8))
    N_I = int(round(Neurons * 0.2))

    C_E = N_E * 0.1

    # Excitatory and inhibitory weights
    J_E = 0.1
    J_I = -g * J_E

    # The firing rate of a neuron in the external pop
    # is the product of eta time the threshold rate
    # the steady state firing rate which is
    # needed to bring a neuron to threshold.
    nu_ex = eta * V_th / (J_E * C_E * tau_m)

    # population rate of the whole external population.
    # With CE neurons the pop rate is simply the product
    # nu_ex*C_E  the factor 1000.0 changes the units from
    # spikes per ms to spikes per second.
    p_rate = 1000.0 * nu_ex * C_E
    print "Rate is: %f HZ" % (p_rate / 1000)

    # Neural Parameters
    pynn.setup(timestep=1.0, min_delay=1.0, max_delay=16.0)

    if simulator_Name == "spiNNaker":

        # Makes it easy to scale up the number of cores
        pynn.set_number_of_neurons_per_core("IF_curr_exp", 100)
        pynn.set_number_of_neurons_per_core("SpikeSourcePoisson", 100)

    rng = NumpyRNG(seed=1)

    RandomDistribution('uniform', [-10.0, 0.0], rng)
    RandomDistribution('uniform', [-10.0, 0.0], rng)

    exc_cell_params = {
        'cm': 1.0,  # pf
        'tau_m': tau_m,
        'tau_refrac': tau_ref,
        'v_rest': v_rest,
        'v_reset': v_reset,
        'v_thresh': V_th,
        'tau_syn_E': tauSyn,
        'tau_syn_I': tauSyn,
        'i_offset': 0.9
    }

    inh_cell_params = {
        'cm': 1.0,  # pf
        'tau_m': tau_m,
        'tau_refrac': tau_ref,
        'v_rest': v_rest,
        'v_reset': v_reset,
        'v_thresh': V_th,
        'tau_syn_E': tauSyn,
        'tau_syn_I': tauSyn,
        'i_offset': 0.9
    }

    # Set-up pynn Populations
    E_pop = pynn.Population(N_E, pynn.IF_curr_exp, exc_cell_params,
                            label="E_pop")

    I_pop = pynn.Population(N_I, pynn.IF_curr_exp, inh_cell_params,
                            label="I_pop")

    Poiss_ext_E = pynn.Population(N_E, pynn.SpikeSourcePoisson, {'rate': 10.0},
                                  label="Poisson_pop_E")
    Poiss_ext_I = pynn.Population(N_I, pynn.SpikeSourcePoisson, {'rate': 10.0},
                                  label="Poisson_pop_I")

    # Connectors
    E_conn = pynn.FixedProbabilityConnector(epsilon, weights=J_E, delays=delay)
    I_conn = pynn.FixedProbabilityConnector(epsilon, weights=J_I, delays=delay)

    # Use random delays for the external noise and
    # set the inital membrance voltage below the resting potential
    # to avoid the overshoot of activity in the beginning of the simulation
    rng = NumpyRNG(seed=1)
    delay_distr = RandomDistribution('uniform', [1.0, 16.0], rng=rng)
    Ext_conn = pynn.OneToOneConnector(weights=J_E * 10, delays=delay_distr)

    uniformDistr = RandomDistribution('uniform', [-10, 0], rng)
    E_pop.initialize('v', uniformDistr)
    I_pop.initialize('v', uniformDistr)

    # Projections
    pynn.Projection(E_pop, E_pop, E_conn, target="excitatory")
    pynn.Projection(I_pop, E_pop, I_conn, target="inhibitory")
    pynn.Projection(E_pop, I_pop, E_conn, target="excitatory")
    pynn.Projection(I_pop, I_pop, I_conn, target="inhibitory")

    pynn.Projection(Poiss_ext_E, E_pop, Ext_conn, target="excitatory")
    pynn.Projection(Poiss_ext_I, I_pop, Ext_conn, target="excitatory")

    # Record stuff
    if record:
        E_pop.record()
        Poiss_ext_E.record()

    pynn.run(sim_time)

    esp = None
    s = None

    if record:
        esp = E_pop.getSpikes(compatible_output=True)
        s = Poiss_ext_E.getSpikes(compatible_output=True)

    pynn.end()

    return (esp, s, N_E)
