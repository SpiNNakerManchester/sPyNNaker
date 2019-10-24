# Copyright (c) 2017-2019 The University of Manchester
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

import numpy as np
from pyNN.random import NumpyRNG, RandomDistribution
import spynnaker as pynn


def poisson_generator(rate, rng, t_start=0.0, t_stop=1000.0, array=True,
                      debug=False):
    """
    Returns a SpikeTrain whose spikes are a realization of a Poisson process\
    with the given rate (Hz) and stopping time t_stop (milliseconds).

    Note: t_start is always 0.0, thus all realizations are as if\
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
    return [round(x) for x in spikes]


def do_run(Neurons, sim_time, record, seed=None):
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
    v_th = 20.0
    v_rest = 0.0
    tau_syn = 1.0

    n_e = int(round(Neurons * 0.8))
    n_i = int(round(Neurons * 0.2))

    c_e = n_e * 0.1

    # Excitatory and inhibitory weights
    j_e = 0.1
    j_i = -g * j_e

    # The firing rate of a neuron in the external pop
    # is the product of eta time the threshold rate
    # the steady state firing rate which is
    # needed to bring a neuron to threshold.
    nu_ex = eta * v_th / (j_e * c_e * tau_m)

    # population rate of the whole external population.
    # With CE neurons the pop rate is simply the product
    # nu_ex*c_e  the factor 1000.0 changes the units from
    # spikes per ms to spikes per second.
    p_rate = 1000.0 * nu_ex * c_e
    print("Rate is: %f HZ" % (p_rate / 1000))

    # Neural Parameters
    pynn.setup(timestep=1.0, min_delay=1.0, max_delay=16.0)

    # Makes it easy to scale up the number of cores
    pynn.set_number_of_neurons_per_core(pynn.IF_curr_exp, 100)
    pynn.set_number_of_neurons_per_core(pynn.SpikeSourcePoisson, 100)

    exc_cell_params = {
        'cm': 1.0,  # pf
        'tau_m': tau_m,
        'tau_refrac': tau_ref,
        'v_rest': v_rest,
        'v_reset': v_reset,
        'v_thresh': v_th,
        'tau_syn_E': tau_syn,
        'tau_syn_I': tau_syn,
        'i_offset': 0.9
    }

    inh_cell_params = {
        'cm': 1.0,  # pf
        'tau_m': tau_m,
        'tau_refrac': tau_ref,
        'v_rest': v_rest,
        'v_reset': v_reset,
        'v_thresh': v_th,
        'tau_syn_E': tau_syn,
        'tau_syn_I': tau_syn,
        'i_offset': 0.9
    }

    # Set-up pynn Populations
    e_pop = pynn.Population(n_e, pynn.IF_curr_exp(**exc_cell_params),
                            label="e_pop")

    i_pop = pynn.Population(n_i, pynn.IF_curr_exp, inh_cell_params,
                            label="i_pop")

    if seed is None:
        poisson_ext_e = pynn.Population(
            n_e, pynn.SpikeSourcePoisson(rate=10.0),
            label="Poisson_pop_E")
        poisson_ext_i = pynn.Population(
            n_i, pynn.SpikeSourcePoisson(rate=10.0),
            label="Poisson_pop_I")
    else:
        poisson_ext_e = pynn.Population(
            n_e, pynn.SpikeSourcePoisson(rate=10.0),
            label="Poisson_pop_E", additional_parameters={"seed": seed})
        poisson_ext_i = pynn.Population(
            n_i, pynn.SpikeSourcePoisson(rate=10.0),
            label="Poisson_pop_I", additional_parameters={"seed": seed+1})

    # Connectors
    rng = NumpyRNG(seed=seed)
    e_conn = pynn.FixedProbabilityConnector(epsilon, rng=rng)
    i_conn = pynn.FixedProbabilityConnector(epsilon, rng=rng)

    # Use random delays for the external noise and
    # set the initial membrane voltage below the resting potential
    # to avoid the overshoot of activity in the beginning of the simulation
    delay_distr = RandomDistribution('uniform', [1.0, 16.0], rng=rng)
    ext_conn = pynn.OneToOneConnector()

    uniform_distr = RandomDistribution('uniform', [-10, 0], rng=rng)
    e_pop.initialize(v=uniform_distr)
    i_pop.initialize(v=uniform_distr)

    # Projections
    pynn.Projection(
        presynaptic_population=e_pop, postsynaptic_population=e_pop,
        connector=e_conn, receptor_type="excitatory",
        synapse_type=pynn.StaticSynapse(weight=j_e, delay=delay_distr))
    pynn.Projection(
        presynaptic_population=i_pop, postsynaptic_population=e_pop,
        connector=i_conn, receptor_type="inhibitory",
        synapse_type=pynn.StaticSynapse(weight=j_i, delay=delay))
    pynn.Projection(
        presynaptic_population=e_pop, postsynaptic_population=i_pop,
        connector=e_conn, receptor_type="excitatory",
        synapse_type=pynn.StaticSynapse(weight=j_e, delay=delay_distr))
    pynn.Projection(
        presynaptic_population=i_pop, postsynaptic_population=i_pop,
        connector=i_conn, receptor_type="inhibitory",
        synapse_type=pynn.StaticSynapse(weight=j_i, delay=delay))

    pynn.Projection(
        presynaptic_population=poisson_ext_e, postsynaptic_population=e_pop,
        connector=ext_conn, receptor_type="excitatory",
        synapse_type=pynn.StaticSynapse(weight=j_e * 10, delay=delay_distr))
    pynn.Projection(
        presynaptic_population=poisson_ext_i, postsynaptic_population=i_pop,
        connector=ext_conn, receptor_type="excitatory",
        synapse_type=pynn.StaticSynapse(weight=j_e * 10, delay=delay_distr))

    # Record stuff
    if record:
        e_pop.record('spikes')
        poisson_ext_e.record('spikes')

    pynn.run(sim_time)

    esp = None
    s = None

    if record:
        esp = e_pop.get_data('spikes')
        s = poisson_ext_e.get_data('spikes')

    pynn.end()

    return esp, s, n_e
