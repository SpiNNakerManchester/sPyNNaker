from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class IFCurrentAlphaPopulation(AbstractIntegrateAndFireProperties,
                               AbstractPopulationVertex):
    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, constraints=None,
                 label=None, tau_m=20,
                 cm=1.0, v_rest=-65.0, v_reset=-65.0, v_thresh=-50.0,
                 tau_syn_E=0.5, tau_syn_I=0.5, tau_refrac=0.1, i_offset=0,
                 v_init=None):
        """
        Leaky integrate and fire model with fixed threshold and alpha-function-\
        shaped post-synaptic current.
        """
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def get_cpu_usage_for_atoms(self, vertex_slice):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def model_name(self):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def get_parameters(self):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")