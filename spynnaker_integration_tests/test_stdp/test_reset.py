import pyNN.utility.plotting as plot
import matplotlib.pyplot as plt
import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestReset(BaseTestCase):

    def resetter(self):
        n_neurons = 100
        simtime = 5000

        sim.setup(timestep=1.0)

        pre_pop = sim.Population(n_neurons, sim.IF_curr_exp(), label="Pre")
        post_pop = sim.Population(n_neurons, sim.IF_curr_exp(), label="Post")
        pre_noise = sim.Population(
            n_neurons, sim.SpikeSourcePoisson(rate=10.0), label="Noise_Pre")
        post_noise = sim.Population(
            n_neurons, sim.SpikeSourcePoisson(rate=10.0), label="Noise_Post")

        pre_pop.record("spikes")
        post_pop.record("spikes")

        training = sim.Population(
            n_neurons,
            sim.SpikeSourcePoisson(rate=10.0, start=1500.0, duration=1500.0),
            label="Training")

        sim.Projection(pre_noise,  pre_pop,  sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=2.0))
        sim.Projection(post_noise, post_pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=2.0))

        sim.Projection(training, pre_pop,  sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5.0, delay=1.0))
        sim.Projection(training, post_pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5.0, delay=10.0))

        timing_rule = sim.SpikePairRule(tau_plus=20.0, tau_minus=20.0,
                                        A_plus=0.5, A_minus=0.5)
        weight_rule = sim.AdditiveWeightDependence(w_max=5.0, w_min=0.0)

        partner_selection_last_neuron = sim.RandomSelection()
        formation_distance = sim.DistanceDependentFormation(
            grid=[numpy.sqrt(n_neurons), numpy.sqrt(n_neurons)],
            sigma_form_forward=.5  # spread of feed-forward connections
        )
        elimination_weight = sim.RandomByWeightElimination(
            # no eliminations for potentiated synapses
            prob_elim_potentiated=0,
            prob_elim_depressed=0,  # no elimination for depressed synapses
            # Use same weight as initial weight for static connections
            threshold=0.5
        )
        structure_model_with_stdp = sim.StructuralMechanismSTDP(
            # Partner selection, formation and elimination rules from above
            partner_selection_last_neuron, formation_distance,
            elimination_weight,
            # Use this weight when creating a new synapse
            initial_weight=0,
            # Use this weight for synapses at start of simulation
            weight=0,
            # Use this delay when creating a new synapse
            initial_delay=5,
            # Use this weight for synapses at the start of simulation
            delay=5,
            # Maximum allowed fan-in per target-layer neuron
            s_max=64,
            # Frequency of rewiring in Hz
            f_rew=10 ** 4,
            # STDP rules
            timing_dependence=sim.SpikePairRule(
                tau_plus=20., tau_minus=20.0, A_plus=0.5, A_minus=0.5),
            weight_dependence=sim.AdditiveWeightDependence(w_min=0, w_max=5.)
        )

        plastic_projection = sim.Projection(
            pre_pop, post_pop,
            sim.FixedProbabilityConnector(0.),  # No initial connections
            synapse_type=structure_model_with_stdp,
            label="structurally_plastic_projection"
        )

        sim.run(simtime)
        w1 = plastic_projection.getWeights()
        sim.reset()
        sim.run(simtime)
        w2 = plastic_projection.getWeights()
        pre_neo = pre_pop.get_data(variables=["spikes"])
        pre_spikes = pre_neo.segments[1].spiketrains

        post_neo = post_pop.get_data(variables=["spikes"])
        post_spikes = post_neo.segments[1].spiketrains

        print(w2)

        sim.end()

    def test_resetter(self):
        return
        self.runsafe(self.resetter)
