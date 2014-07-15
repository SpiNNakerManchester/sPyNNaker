import math

from pacman103.lib import data_spec_constants
from pacman103.front.common.exp_population_vertex import ExponentialPopulationVertex
from pacman103.front.common.if_properties import IF_Properties
from pacman103.front.common.neuron_parameter import NeuronParameter

class IF_ConductanceExponentialPopulation(ExponentialPopulationVertex,
                                          IF_Properties,
                                          PopulationVertex):
    core_app_identifier = data_spec_constants.IF_CURR_EXP_CORE_APPLICATION_ID

    def __init__( self, n_neurons, constraints = None, label = None,
                  tau_m = 20, cm = 1.0, e_rev_E = 0.0, e_rev_I = -70.0,
                  v_rest = -65.0, v_reset = -65.0, v_thresh = -50.0,
                  tau_syn_E = 5.0, tau_syn_I = 5.0, tau_refrac = 0.1,
                  i_offset = 0):
        # Instantiate the parent class
        super( IF_ConductanceExponentialPopulation, self ).__init__(
            n_neurons = n_neurons,
            n_params = 12,
            binary = "IF_cond_exp.aplx",
            constraints = constraints,
            label = label,
            tau_syn_E = tau_syn_E,
            tau_syn_I = tau_syn_I
        )

        # Save the parameters
        self.tau_m = self.convert_param(tau_m, n_neurons)
        self.cm =  self.convert_param(cm, n_neurons)
        self.e_rev_E =  self.convert_param(e_rev_E, n_neurons)
        self.e_rev_I = self.convert_param(e_rev_I, n_neurons)
        self.v_rest =  self.convert_param(v_rest, n_neurons)
        self.v_reset =  self.convert_param(v_reset, n_neurons)
        self.v_thresh =  self.convert_param(v_thresh, n_neurons)
        self.tau_refrac =  self.convert_param(tau_refrac, n_neurons)
        self.i_offset =  self.convert_param(i_offset, n_neurons)
        self.v_init =  self.convert_param(v_rest, n_neurons)

    @property
    def refract_timer( self ):
        return 0

    @property
    def t_refract( self ):
        return self.tau_refrac

    @property
    def model_name( self ):
        return "IF_curr_exp"
    
    def getCPU(self, lo_atom, hi_atom):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 782 * ((hi_atom - lo_atom) + 1)
    
    def get_maximum_atoms_per_core(self):
        '''
        returns the maxiumum number of atoms that a core can support
        for this model
        '''
        return 256

    def get_parameters(self, machineTimeStep):
        """
        Generate Neuron Parameter data (region 2):
        """

        # Get the parameters
        #typedef struct neuron_t {
        #
        #// nominally 'fixed' parameters
        #    REAL     V_thresh;   // membrane voltage threshold at which neuron spikes [mV]
        #    REAL     V_reset;    // post-spike reset membrane voltage    [mV]
        #    REAL     V_rest;     // membrane resting voltage [mV]
        #    REAL     R_membrane; // membrane resistance [MegaOhm] 
        #    
        #    REAL        V_rev_E;        // reversal voltage - Excitatory    [mV]
        #    REAL        V_rev_I;        // reversal voltage - Inhibitory    [mV]
        #    
        #// variable-state parameter
        #    REAL     V_membrane; // membrane voltage [mV]
        #
        #// late entry! Jan 2014 (trickle current)
        #    REAL        I_offset;    // offset current [nA] but take care because actually 'per timestep charge'
        #    
        #// 'fixed' computation parameter - time constant multiplier for closed-form solution
        #    REAL     exp_TC;        // exp( -(machine time step in ms)/(R * C) ) [.]
        #    
        #// for ODE solution only
        #    REAL      one_over_tauRC; // [kHz!] only necessary if one wants to use ODE solver because allows * and host double prec to calc - UNSIGNED ACCUM & unsigned fract much slower
        #
        #// refractory time information
        #    int32_t refract_timer; // countdown to end of next refractory period [ms/10] - 3 secs limit do we need more? Jan 2014
        #    int32_t T_refract;      // refractory time of neuron [ms/10]
        return [
            NeuronParameter(self.v_thresh,                    's1615',   1.0 ),
            NeuronParameter(self.v_reset,                     's1615',   1.0 ),
            NeuronParameter(self.v_rest,                      's1615',   1.0 ),
            NeuronParameter(self.r_membrane(machineTimeStep), 's1615',   1.0 ),
            NeuronParameter(self.e_rev_E,                     's1615',   1.0 ),
            NeuronParameter(self.e_rev_I,                     's1615',   1.0 ),
            NeuronParameter(self.v_init,                      's1615',   1.0 ),
            NeuronParameter(self.ioffset(machineTimeStep),    's1615',   1.0 ),
            NeuronParameter(self.exp_tc(machineTimeStep),     's1615',   1.0 ),
            NeuronParameter(self.one_over_tauRC,              's1615',   1.0 ),
            NeuronParameter(self.refract_timer,               'uint32',  1.0 ),
            NeuronParameter(self.t_refract,                   'uint32', 10.0 ),
        ]
