
import spynnaker.pyNN as sim
import numpy
import unittest

# How large should the population of excitatory neurons be?
# (Number of inhibitory neurons is proportional to this)
NUM_EXCITATORY = 2000


class TestSTDPGetWeightsWith2dMasterPop(unittest.TestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    
    def build_network(self, dynamics, cell_params):
        """
        Function to build the basic network - dynamics should be a PyNN
         synapse dynamics object
:param dynamics: 
:return:
        """
        # SpiNNaker setup
        model = sim.IF_curr_exp
        sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

        # Create excitatory and inhibitory populations of neurons
        ex_pop = sim.Population(NUM_EXCITATORY, model, cell_params)
        in_pop = sim.Population(NUM_EXCITATORY / 4, model, cell_params)

        # Record excitatory spikes
        ex_pop.record()

        # Make excitatory->inhibitory projections
        sim.Projection(ex_pop, in_pop, sim.FixedProbabilityConnector(
            0.02, weights=0.03), target='excitatory')
        sim.Projection(ex_pop, ex_pop, sim.FixedProbabilityConnector(
            0.02, weights=0.03), target='excitatory')

        # Make inhibitory->inhibitory projections
        sim.Projection(in_pop, in_pop, sim.FixedProbabilityConnector(
            0.02, weights=-0.3), target='inhibitory')

        # Make inhibitory->excitatory projections
        ie_projection = sim.Projection(
            in_pop, ex_pop, sim.FixedProbabilityConnector(0.02, weights=0),
            target='inhibitory', synapse_dynamics=dynamics)

        return ex_pop, ie_projection
    
    def test_get_weights(self):
        # Population parameters
        cell_params = {
            'cm': 0.2,  # nF
            'i_offset': 0.2,
            'tau_m': 20.0,
            'tau_refrac': 5.0,
            'tau_syn_E': 5.0,
            'tau_syn_I': 10.0,
            'v_reset': -60.0,
            'v_rest': -60.0,
            'v_thresh': -50.0
        }

        # Reduce number of neurons to simulate on each core
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        # Build inhibitory plasticity  model
        stdp_model = sim.STDPMechanism(
            timing_dependence=sim.SpikePairRule(
                tau_plus=20.0, tau_minus=12.7, nearest=True),
            weight_dependence=sim.AdditiveWeightDependence(
                w_min=0.0, w_max=1.0, A_plus=0.05),
            mad=True
        )

        # Build plastic network
        plastic_ex_pop, plastic_ie_projection =\
            self.build_network(sim.SynapseDynamics(slow=stdp_model), 
                               cell_params)

        # Run simulation
        sim.run(10000)

        # Get plastic spikes and save to disk
        plastic_spikes = plastic_ex_pop.getSpikes(compatible_output=True)
        #numpy.save("plastic_spikes.npy", plastic_spikes)

        plastic_weights = plastic_ie_projection.getWeights(format="array")
        #  mean_weight = numpy.average(plastic_weights)

        # End simulation on SpiNNaker
        sim.end()

if __name__ == '__main__':
    unittest.main()