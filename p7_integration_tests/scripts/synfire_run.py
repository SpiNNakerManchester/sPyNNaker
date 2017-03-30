"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p
# This is a constraint that really knows about SpiNNaker...
from pacman.model.constraints.placer_constraints\
    .placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint


def do_run(nNeurons, spike_times=[[0]], delay=17,
           neurons_per_core=10, constraint=None, spike_times_list=None,
           runtimes=[1000], reset=False, extract_between_runs=True, new_pop=False,
           record=True, record_v=True, record_gsyn=True, get_weights=False):
    """

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param spike_times: times the inputer sends in spikes
    :type spike_times: matrix of int times the inputer sends in spikes
    :param spike_times_list: list of times the inputer sends in spikes
        - must be the same length as  runtimes
        - If set the spike_time parameter is ignored
    :type spike_times: list of matrix of int times the inputer sends in spikes
    :param delay: time delay in the single connectors in the spike chain
    :type delay: int
    :param neurons_per_core: Number of neurons per core.
        If set to None no  set_number_of_neurons_per_core call will be made
    :type neurons_per_core: int or None
    :param constraint: A Constraint to be place on populations[0]
    :type constraint: AbstractConstraint
    :param runtimes: times for each run
    :type runtimes: list of int
    :param reset: if True will call reset after each run except the last
    :type reset: bool
    :param extract_between_runs: If True reads V, gysn and spikes
        between each run.
    :type extract_between_runs: bool
    :param new_pop: If True will add a new population before the second run
    :type new_pop: bool
    :param record: If True will aks for spikes to be recorded
    :type record: bool
    :param record_v: If True will aks for voltage to be recorded
    :type record_v: bool
    :param record_gsyn: If True will aks for gsyn to be recorded
    :type record_gsun: bool
    :param get_weights: If True set will add a weight value to the return
    :type get_weights: bool
    :return (v, gsyn, spikes, weights .....)
        v: Volage after last or each run (if requested else None)
        gysn: gysn after last or each run (if requested else None)
        spikes: spikes after last or each run (if requested else None)
        weights: weights after last or each run (if requested else skipped)

        All three/four values will repeated once per run is requested
    """
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    if neurons_per_core is not None:
        p.set_number_of_neurons_per_core("IF_curr_exp", neurons_per_core)

    cell_params_lif = {'cm': 0.25,
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0
                       }

    populations = list()
    projections = list()

    weight_to_spike = 2.0

    loopConnections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        loopConnections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, 1)]

    run_count = 0
    if spike_times_list is None:
        spikeArray = {'spike_times': spike_times}
    else:
        spikeArray = {'spike_times': spike_times_list[run_count]}

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                       label='pop_1'))
    if constraint is not None:
        populations[0].set_constraint(constraint)

    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                       label='inputSpikes_1'))

    projections.append(p.Projection(populations[0], populations[0],
                       p.FromListConnector(loopConnections)))
    projections.append(p.Projection(populations[1], populations[0],
                       p.FromListConnector(injectionConnection)))

    if record_v:
        populations[0].record_v()
    if record_gsyn:
        populations[0].record_gsyn()
    if record:
        populations[0].record()

    results = ()

    for runtime in runtimes[:-1]:
        p.run(runtime)
        run_count += 1

        if extract_between_runs:
            results += _get_data(populations[0], record, record_v, record_gsyn)
            if get_weights:
                results += (projections[0].getWeights(), )

        if new_pop:
            populations.append(
                p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                             label='pop_2'))
            injectionConnection = [(nNeurons - 1, 0, weight_to_spike, 1)]
            new_proj = p.Projection(populations[0], populations[2],
                                    p.FromListConnector(injectionConnection))
            projections.append(new_proj)

        if spike_times_list is not None:
            populations[1].tset("spike_times", spike_times_list[run_count])

        if reset:
            p.reset()

    p.run(runtimes[-1])

    results += _get_data(populations[0], record, record_v, record_gsyn)
    if get_weights:
        results += (projections[0].getWeights(), )

    p.end()

    return results


def _get_data(population, record, record_v, record_gsyn):
    if record_v:
        v = population.get_v(compatible_output=True)
    else:
        v = None
    if record_gsyn:
        gsyn = population.get_gsyn(compatible_output=True)
    else:
        gsyn = None
    if record:
        spikes = population.getSpikes(compatible_output=True)
    else:
        spikes = None

    return (v, gsyn, spikes)
