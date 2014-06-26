from pacman103.lib import data_spec_constants
from pacman103.front.common.exp_population_vertex import ExponentialPopulationVertex
from pacman103.front.common.neuron_parameter import NeuronParameter
import numpy

class Izhikevich_CurrentExponentialPopulation( ExponentialPopulationVertex ):
    core_app_identifier = data_spec_constants.IF_CURR_EXP_CORE_APPLICATION_ID
    
    def __init__( self, n_neurons, constraints = None, label = None,
                  a = 0.02, c = -65.0, b = 0.2, d = 2.0, 
                  i_offset = 0,
                  u_init = -14.0, v_init = -70.0,
                  tau_syn_E = 5.0, tau_syn_I = 5.0):
        # Instantiate the parent class
        super( Izhikevich_CurrentExponentialPopulation, self ).__init__(
            n_neurons = n_neurons,
            n_params = 8,
            binary = "IZK_curr_exp.aplx",
            constraints = constraints,
            label = label,
            tau_syn_E = tau_syn_E,
            tau_syn_I = tau_syn_I
        )

        # Save the parameters
        self.a = self.convert_param(a, n_neurons)
        self.b = self.convert_param(b, n_neurons)
        self.c = self.convert_param(c, n_neurons)
        self.d = self.convert_param(d, n_neurons)
        self.v_init = self.convert_param(v_init, n_neurons)
        self.u_init = self.convert_param(u_init, n_neurons)
        self.i_offset = self.convert_param(i_offset, n_neurons)

    def initialize_v(self, value):
        self.v_init = self.convert_param(value, self.atoms)
        
    def initialize_u(self, value):
        self.u_init = self.convert_param(value, self.atoms)

    @property
    def model_name( self ):
        return "IZK_curr_exp"
    
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
    
    def ioffset(self, machineTimeStep):
        return self.i_offset / (1000.0 / float(machineTimeStep))

    def get_parameters(self, machineTimeStep):
        """
        Generate Neuron Parameter data (region 2):
        """

        # Get the parameters:
        # typedef struct neuron_t {
        #
        # // nominally 'fixed' parameters
        #     REAL         A;
        #     REAL         B;
        #     REAL         C;            
        #     REAL         D;
        #
        # // Variable-state parameters
        #     REAL         V;
        #     REAL         U;
        #
        # // offset current [nA]
        #     REAL         I_offset;
        # 
        # // current timestep - simple correction for threshold in beta version   
        #     REAL         this_h;  
        # } neuron_t;
        return [
            NeuronParameter( self.a,                        's1615',   1.0),
            NeuronParameter( self.b,                        's1615',   1.0),
            NeuronParameter( self.c,                        's1615',   1.0),
            NeuronParameter( self.d,                        's1615',   1.0),
            NeuronParameter( self.v_init,                   's1615',   1.0),
            NeuronParameter( self.u_init,                   's1615',   1.0),
            NeuronParameter( self.ioffset(machineTimeStep), 's1615',   1.0),
            NeuronParameter( 0,                             's1615',   1.0)
        ]
        

