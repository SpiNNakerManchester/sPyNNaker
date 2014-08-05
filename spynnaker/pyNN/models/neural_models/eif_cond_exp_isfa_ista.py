from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_conductive_vertex \
    import AbstractConductiveVertex


class EIFConductanceExponentialPopulation(AbstractExponentialPopulationVertex,
                                          AbstractConductiveVertex,
                                          AbstractIntegrateAndFireProperties,
                                          AbstractPopulationVertex):

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, constraints=None, label=None, tau_m=9.3667,
                 cm=0.281, v_rest=-70.6, v_reset=-70.6, v_thresh=-50.0,
                 tau_syn_E=5.0, tau_syn_I=0.5, tau_refrac=0.1, i_offset=0.0,
                 a=4.0, b=0.0805, v_spike=-40.0, tau_w=144.0, e_rev_E=0.0,
                 e_rev_I=-70.0, delta_T=2.0, v_init=None):
        """
        Exponential integrate and fire neuron with spike triggered and \
        sub-threshold adaptation currents (isfa, ista reps.)
        """
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

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")
