import math

from pacman103.lib import data_spec_constants
from pacman103.front.common.dual_exp_population_vertex import DualExponentialPopulationVertex
from pacman103.front.common.if_properties import IF_Properties
from pacman103.front.common.neuron_parameter import NeuronParameter

class IF_CurrentDualExponentialPopulation(DualExponentialPopulationVertex,
                                          IF_Properties):
    core_app_identifier = data_spec_constants.IF_CURR_EXP_CORE_APPLICATION_ID

    def __init__( self, n_neurons, constraints = None, label = None,
                  tau_m = 20.0, cm = 1.0, 
                  v_rest = -65.0, v_reset = -65.0, v_thresh = -50.0,
                  tau_syn_E = 5.0, tau_syn_E2 = 5.0, tau_syn_I = 5.0, 
                  tau_refrac = 0.1, i_offset = 0, v_init = None):
        # Instantiate the parent class
        super( IF_CurrentDualExponentialPopulation, self ).__init__(
            n_neurons = n_neurons,
            n_params = 10,
            binary = "IF_curr_exp_dual.aplx",
            constraints = constraints,
            label = label,
            tau_syn_E = tau_syn_E,
            tau_syn_E2 = tau_syn_E2,
            tau_syn_I = tau_syn_I
        )

        # Save the parameters
        self.tau_m = self.convert_param(tau_m, n_neurons)
        self.cm = self.convert_param(cm, n_neurons)
        self.v_rest = self.convert_param(v_rest, n_neurons)
        self.v_reset = self.convert_param(v_reset, n_neurons)
        self.v_thresh = self.convert_param(v_thresh, n_neurons)
        self.tau_refrac = self.convert_param(tau_refrac, n_neurons)
        self.i_offset = self.convert_param(i_offset, n_neurons)
        self.v_init = self.convert_param(v_rest, n_neurons)
        if v_init is not None:
            self.v_init = self.convert_param(v_init, n_neurons)
        self.ringbuffer_saturation_scaling = 32 # Max accumulated ringbuffer value
                                                # in 'weight units' used to scale
                                                # weight value to a fraction

    @property
    def refract_timer( self ):
        return 0

    @property
    def t_refract( self ):
        return self.tau_refrac

    @property
    def model_name( self ):
        return "IF_curr_dual_exp"
    
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
        return [
            NeuronParameter(self.v_thresh,                    's1615',   1.0 ),
            NeuronParameter(self.v_reset,                     's1615',   1.0 ),
            NeuronParameter(self.v_rest,                      's1615',   1.0 ),
            NeuronParameter(self.r_membrane(machineTimeStep), 's1615',   1.0 ),
            NeuronParameter(self.v_init,                      's1615',   1.0 ),
            NeuronParameter(self.ioffset(machineTimeStep),    's1615',   1.0 ),
            NeuronParameter(self.exp_tc(machineTimeStep),     's1615',   1.0 ),
            NeuronParameter(self.one_over_tauRC,              's1615',   1.0 ),
            NeuronParameter(self.refract_timer,               'uint32',  1.0 ),
            NeuronParameter(self.t_refract,                   'uint32', 10.0 ),
        ]
