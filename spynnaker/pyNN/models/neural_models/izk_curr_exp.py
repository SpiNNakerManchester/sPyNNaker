from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_Izhikevich_vertex \
    import AbstractIzhikevichVertex
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class IzhikevichCurrentExponentialPopulation(AbstractIzhikevichVertex,
                                             AbstractExponentialPopulationVertex,
                                             AbstractPopulationVertex):

    CORE_APP_IDENTIFIER = constants.IZK_CURRENT_EXP_CORE_APPLICATION_ID

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, constraints=None, label=None, a=0.02, c=-65.0,
                 b=0.2, d=2.0, i_offset=0, u_init=-14.0, v_init=-70.0,
                 tau_syn_E=5.0, tau_syn_I=5.0):

        # Instantiate the parent classes
        AbstractExponentialPopulationVertex.__init__(self, n_neurons=n_neurons,
                                                     tau_syn_e=tau_syn_E,
                                                     tau_syn_i=tau_syn_I)
        AbstractIzhikevichVertex.__init__(self, n_neurons, a=a, c=c, b=b, d=d,
                                          i_offset=i_offset, u_init=u_init,
                                          v_init=v_init)
        AbstractPopulationVertex.__init__(self, n_neurons=n_neurons,
                                          n_params=10, label=label,
                                          max_atoms_per_core=256,
                                          binary="IZK_curr_exp.aplx",
                                          constraints=constraints)

    @property
    def model_name(self):
        return "IZK_curr_exp"
    
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 782 * ((hi_atom - lo_atom) + 1)

    def get_parameters(self):
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
            NeuronParameter(self.a, 's1615'),
            NeuronParameter(self.b, 's1615'),
            NeuronParameter(self.c, 's1615'),
            NeuronParameter(self.d, 's1615'),
            NeuronParameter(self.v_init, 's1615'),
            NeuronParameter(self.u_init, 's1615'),
            NeuronParameter(self.ioffset(self._machine_time_step), 's1615'),
            NeuronParameter(0, 's1615')
        ]