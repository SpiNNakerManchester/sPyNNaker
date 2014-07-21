from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_duel_exponential_vertex \
    import AbstractDualExponentialVertex
from spynnaker.pyNN.models.neural_properties.integrate_and_fire_properties \
    import IntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class IFCurrentDualExponentialPopulation(AbstractDualExponentialVertex,
                                         IntegrateAndFireProperties,
                                         AbstractPopulationVertex):
    CORE_APP_IDENTIFIER = constants.IF_CURRENT_EXP_CORE_APPLICATION_ID

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, constraints=None, label=None,
                 tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0, 
                 v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, 
                 tau_refrac=0.1, i_offset=0, v_init=None):
        
        # Instantiate the parent classes
        AbstractDualExponentialVertex.__init__(self, n_neurons=n_neurons,
                                               tau_syn_E=tau_syn_E,
                                               tau_syn_E2=tau_syn_E2,
                                               tau_syn_I=tau_syn_I)
        IntegrateAndFireProperties.__init__(self, atoms=n_neurons, cm=cm,
                                            tau_m=tau_m, i_offset=i_offset,
                                            v_init=v_init, v_reset=v_reset,
                                            v_rest=v_rest, v_thresh=v_thresh,
                                            tau_refrac=tau_refrac)
        AbstractPopulationVertex.__init__(self, n_neurons=n_neurons,
                                          n_params=10, label=label,
                                          max_atoms_per_core=256,
                                          binary="IF_curr_exp_dual.aplx",
                                          constraints=constraints)

    @property
    def model_name(self):
        return "IF_curr_dual_exp"
    
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 782 * ((hi_atom - lo_atom) + 1)

    def get_parameters(self):
        """
        Generate Neuron Parameter data (region 2):
        """
        
        # Get the parameters
        return [
            NeuronParameter(self.v_thresh, 's1615'),
            NeuronParameter(self.v_reset, 's1615'),
            NeuronParameter(self.v_rest, 's1615'),
            NeuronParameter(self.r_membrane(self._machine_time_step), 's1615'),
            NeuronParameter(self.v_init, 's1615'),
            NeuronParameter(self.ioffset(self._machine_time_step), 's1615'),
            NeuronParameter(self.exp_tc(self._machine_time_step), 's1615'),
            NeuronParameter(self.one_over_tauRC, 's1615'),
            NeuronParameter(self.refract_timer, 'uint32'),
            NeuronParameter(self.scaled_t_refract(), 'uint32')
        ]
