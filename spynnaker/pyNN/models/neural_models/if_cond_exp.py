from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.abstract_models.abstract_conductance_vertex \
    import AbstractConductanceVertex


class IFConductanceExponentialPopulation(AbstractExponentialPopulationVertex,
                                         AbstractConductanceVertex,
                                         AbstractIntegrateAndFireProperties,
                                         AbstractPopulationVertex):

    CORE_APP_IDENTIFIER = constants.IF_CONDUCTIVE_EXP_CORE_APPLICATION_ID
    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, tau_m=20, cm=1.0, e_rev_E=0.0, e_rev_I=-70.0,
                 v_rest=-65.0, v_reset=-65.0, v_thresh=-50.0, tau_syn_E=5.0,
                 tau_syn_I=5.0, tau_refrac=0.1, i_offset=0, v_init=None):

        # Instantiate the parent classes
        AbstractConductanceVertex.__init__(self, n_neurons, e_rev_E=e_rev_E,
                                          e_rev_I=e_rev_I)
        AbstractExponentialPopulationVertex.__init__(
            self, n_neurons=n_neurons, tau_syn_E=tau_syn_E,
            tau_syn_I=tau_syn_I, machine_time_step=machine_time_step)
        AbstractIntegrateAndFireProperties.__init__(
            self, atoms=n_neurons, cm=cm, tau_m=tau_m, i_offset=i_offset,
            v_init=v_init, v_reset=v_reset, v_rest=v_rest, v_thresh=v_thresh,
            tau_refrac=tau_refrac)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, n_params=12, label=label,
            max_atoms_per_core=
            IFConductanceExponentialPopulation._model_based_max_atoms_per_core,
            binary="IF_cond_exp.aplx", constraints=constraints,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            weight_scale=AbstractConductanceVertex.WEIGHT_SCALE)
        self._executable_constant = \
            IFConductanceExponentialPopulation.CORE_APP_IDENTIFIER

    @property
    def model_name(self):
        return "IF_cond_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFConductanceExponentialPopulation.\
            _model_based_max_atoms_per_core = new_value

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 781 * ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)

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
            NeuronParameter(self._v_thresh, DataType.S1615),
            NeuronParameter(self._v_reset, DataType.S1615),
            NeuronParameter(self._v_rest, DataType.S1615),
            NeuronParameter(self.r_membrane(self._machine_time_step),
                    DataType.S1615),
            NeuronParameter(self._e_rev_E, DataType.S1615),
            NeuronParameter(self._e_rev_I, DataType.S1615),
            NeuronParameter(self._v_init, DataType.S1615),
            NeuronParameter(self.ioffset(self._machine_time_step),
                    DataType.S1615),
            NeuronParameter(self.exp_tc(self._machine_time_step),
                    DataType.S1615),
            NeuronParameter(self._one_over_tau_rc, DataType.S1615),
            NeuronParameter(self._refract_timer, DataType.UINT32),
            NeuronParameter(self._scaled_t_refract(), DataType.UINT32),
        ]

    def is_population_vertex(self):
        return True

    def is_integrate_and_fire_vertex(self):
        return True

    def is_conductive(self):
        return True

    def is_exp_vertex(self):
        return True

    def is_recordable(self):
        return True
