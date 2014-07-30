from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.neural_properties.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.abstract_models.abstract_conductive_vertex \
    import AbstractConductiveVertex


class IFConductanceExponentialPopulation(AbstractExponentialPopulationVertex,
                                         AbstractConductiveVertex,
                                         AbstractIntegrateAndFireProperties,
                                         AbstractPopulationVertex):
    CORE_APP_IDENTIFIER = constants.IF_CONDUCTIVE_EXP_CORE_APPLICATION_ID
    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, constraints=None, label=None, tau_m=20,
                 cm=1.0, e_rev_E=0.0, e_rev_I=-70.0, v_rest=-65.0,
                 v_reset=-65.0, v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0,
                 tau_refrac=0.1, i_offset=0, v_init=None):
        # Instantiate the parent classes
        AbstractConductiveVertex.__init__(self, n_neurons, e_rev_e=e_rev_E,
                                          e_rev_i=e_rev_I)
        AbstractExponentialPopulationVertex.__init__(self, n_neurons=n_neurons,
                                                     tau_syn_e=tau_syn_E,
                                                     tau_syn_i=tau_syn_I)
        AbstractIntegrateAndFireProperties.__init__(
            self, atoms=n_neurons, cm=cm, tau_m=tau_m, i_offset=i_offset,
            v_init=v_init, v_reset=v_reset, v_rest=v_rest, v_thresh=v_thresh,
            tau_refrac=tau_refrac)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, n_params=10, label=label,
            max_atoms_per_core=
            IFConductanceExponentialPopulation._model_based_max_atoms_per_core,
            binary="IF_cond_exp.aplx", constraints=constraints)

    @property
    def model_name(self):
        return "IF_cond_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFConductanceExponentialPopulation.\
            _model_based_max_atoms_per_core = new_value
    
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
        #typedef struct neuron_t {
        #
        #// nominally 'fixed' parameters
        #    REAL     V_thresh;
        # // membrane voltage threshold at which neuron spikes [mV]
        #    REAL     V_reset;    // post-spike reset membrane voltage    [mV]
        #    REAL     V_rest;     // membrane resting voltage [mV]
        #    REAL     R_membrane; // membrane resistance [MegaOhm] 
        #    
        #    REAL        V_rev_E;
        # // reversal voltage - Excitatory    [mV]
        #    REAL        V_rev_I;
        # // reversal voltage - Inhibitory    [mV]
        #    
        #// variable-state parameter
        #    REAL     V_membrane; // membrane voltage [mV]
        #
        #// late entry! Jan 2014 (trickle current)
        #    REAL        I_offset;
        #  // offset current [nA] but take care because actually
        #     'per timestep charge'
        #    
        #// 'fixed' computation parameter - time constant multiplier for
        #                                   closed-form solution
        #    REAL     exp_TC;
        # // exp( -(machine time step in ms)/(R * C) ) [.]
        #    
        #// for ODE solution only
        #    REAL      one_over_tauRC;
        # // [kHz!] only necessary if one wants to use ODE solver because
        #           allows * and host double prec to calc - UNSIGNED ACCUM &
        #           unsigned fract much slower
        #
        #// refractory time information
        #    int32_t refract_timer; // countdown to end of next refractory
        #                              period [ms/10] - 3 secs limit do we
        #                              need more? Jan 2014
        #    int32_t T_refract;      // refractory time of neuron [ms/10]
        return [
            NeuronParameter(self.v_thresh, 's1615'),
            NeuronParameter(self.v_reset, 's1615'),
            NeuronParameter(self.v_rest, 's1615'),
            NeuronParameter(self.r_membrane(self._machine_time_step), 's1615'),
            NeuronParameter(self.e_rev_E, 's1615'),
            NeuronParameter(self.e_rev_I, 's1615'),
            NeuronParameter(self.v_init, 's1615'),
            NeuronParameter(self.ioffset(self._machine_time_step), 's1615'),
            NeuronParameter(self.exp_tc(self._machine_time_step), 's1615'),
            NeuronParameter(self.one_over_tauRC, 's1615'),
            NeuronParameter(self.refract_timer, 'uint32'),
            NeuronParameter(self.scaled_t_refract(), 'uint32'),
        ]
