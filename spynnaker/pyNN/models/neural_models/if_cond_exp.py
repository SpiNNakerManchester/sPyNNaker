from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_exp_population_vertex import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_conductance_vertex import AbstractConductanceVertex


class IFConductanceExponentialPopulation(
        AbstractExponentialPopulationVertex, AbstractConductanceVertex,
        AbstractIntegrateAndFireProperties,
        AbstractPopulationVertex):

    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, flush_time=None,
                 constraints=None, label=None, tau_m=20, cm=1.0,
                 e_rev_E=0.0, e_rev_I=-70.0, v_rest=-65.0, v_reset=-65.0,
                 v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
                 i_offset=0, v_init=None):

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
            max_atoms_per_core=(IFConductanceExponentialPopulation
                                ._model_based_max_atoms_per_core),
            binary="IF_cond_exp.aplx", constraints=constraints,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            flush_time=flush_time,
            weight_scale=AbstractConductanceVertex.WEIGHT_SCALE)

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

        return [

            # membrane voltage threshold at which neuron spikes [mV]
            # REAL     V_thresh;
            NeuronParameter(self._v_thresh, DataType.S1615),

            # post-spike reset membrane voltage [mV]
            # REAL     V_reset;
            NeuronParameter(self._v_reset, DataType.S1615),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._v_rest, DataType.S1615),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._r_membrane, DataType.S1615),

            # reversal voltage - Excitatory [mV]
            # REAL     V_rev_E;
            NeuronParameter(self._e_rev_E, DataType.S1615),

            # reversal voltage - Inhibitory [mV]
            # REAL     V_rev_I;
            NeuronParameter(self._e_rev_I, DataType.S1615),

            # membrane voltage [mV]
            # REAL     V_membrane;
            NeuronParameter(self._v_init, DataType.S1615),

            # offset current [nA]
            # REAL     I_offset;
            NeuronParameter(self.ioffset, DataType.S1615),

            # 'fixed' computation parameter - time constant multiplier for
            # closed-form solution
            # exp( -(machine time step in ms)/(R * C) )
            # REAL     exp_TC;
            NeuronParameter(self._exp_tc(self._machine_time_step),
                            DataType.S1615),

            # countdown to end of next refractory period [timesteps]
            # int32_t  refract_timer;
            NeuronParameter(self._refract_timer, DataType.INT32),

            # refractory time of neuron [timesteps]
            # int32_t  T_refract;
            NeuronParameter(self._tau_refract_timesteps(
                self._machine_time_step), DataType.INT32),
        ]

    def get_global_parameters(self):
        return []

    def is_population_vertex(self):
        return True

    def is_integrate_and_fire_vertex(self):
        return True

    def is_conductance(self):
        return True

    def is_exp_vertex(self):
        return True

    def is_recordable(self):
        return True
