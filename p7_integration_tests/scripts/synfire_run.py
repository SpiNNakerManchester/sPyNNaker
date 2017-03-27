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


def do_run(nNeurons, runtime=1000, spike_times=[[0]], delay=17,
           neurons_per_core=10, placer_constraint=False,
           record=True, record_v=True, record_gsyn=True):
    """

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param runtime: time for the run
    :type runtime: int
    :param spike_times: times the inputer sends in spikes
    :type spike_times: matrix of int
    :param delay: time delay in the single connectors in the spike chain
    :type delay: int
    :param neurons_per_core: Number of neurons per core
    :type neurons_per_core: int
    :param placer_constraint: if True added a
        PlacerRadialPlacementFromChipConstraint to populations[0]
    :type placer_constraint: bool
    :param record: If True will aks for spikes to be recorded
    :type record: bool
    :param record_v: If True will aks for voltage to be recorded
    :type record_v: bool
    :param record_gsyn: If True will aks for gsyn to be recorded
    :type record_gsun: bool
    :return (v, gsyn, spikes)
        v: Volage after last run (if requested else None)
        gysn: gysn after last run (if requested else None)
        spikes: spikes after last run (if requested else None)
    """
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
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
    spikeArray = {'spike_times': spike_times}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                       label='pop_1'))
    if placer_constraint:
        populations[0].set_constraint(PlacerRadialPlacementFromChipConstraint(3, 3))

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

    p.run(runtime)

    if record_v:
        v = populations[0].get_v(compatible_output=True)
    else:
        v = None
    if record_gsyn:
        gsyn = populations[0].get_gsyn(compatible_output=True)
    else:
        gsyn = None
    if record:
        spikes = populations[0].getSpikes(compatible_output=True)
    else:
        spikes = None

    p.end()

    return (v, gsyn, spikes)
