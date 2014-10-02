from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_dual_exponential_vertex \
    import AbstractDualExponentialVertex
from spynnaker.pyNN.models.abstract_models.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter

from data_specification.enums.data_type import DataType


class IFCurrentDualExponentialPopulation(AbstractDualExponentialVertex,
                                         AbstractIntegrateAndFireProperties,
                                         AbstractPopulationVertex):
    CORE_APP_IDENTIFIER = constants.IF_CURRENT_EXP_CORE_APPLICATION_ID
    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, constraints=None,
                 label=None, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
                 v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, 
                 tau_refrac=0.1, i_offset=0, v_init=None):
        
        # Instantiate the parent classes
        AbstractDualExponentialVertex.__init__(
            self, n_neurons=n_neurons, tau_syn_E=tau_syn_E,
            tau_syn_E2=tau_syn_E2, tau_syn_I=tau_syn_I,
            machine_time_step=machine_time_step)
        AbstractIntegrateAndFireProperties.__init__(
            self, atoms=n_neurons, cm=cm, tau_m=tau_m, i_offset=i_offset,
            v_init=v_init, v_reset=v_reset, v_rest=v_rest, v_thresh=v_thresh,
            tau_refrac=tau_refrac)
        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, n_params=10, label=label,
            binary="IF_curr_exp_dual.aplx", constraints=constraints,
            max_atoms_per_core=
            IFCurrentDualExponentialPopulation._model_based_max_atoms_per_core,
            machine_time_step=machine_time_step)
        self._executable_constant = \
            IFCurrentDualExponentialPopulation.CORE_APP_IDENTIFIER

    @property
    def model_name(self):
        return "IF_curr_dual_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCurrentDualExponentialPopulation.\
            _model_based_max_atoms_per_core = new_value

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 782 * ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)

    def get_parameters(self):
        """
        Generate Neuron Parameter data (region 2):
        """
        
        # Get the parameters
        return [
            NeuronParameter(self._v_thresh, DataType.S1615),
            NeuronParameter(self._v_reset, DataType.S1615),
            NeuronParameter(self._v_rest, DataType.S1615),
            NeuronParameter(self.r_membrane(self._machine_time_step),
                            DataType.S1615),
            NeuronParameter(self._v_init, DataType.S1615),
            NeuronParameter(self.ioffset(self._machine_time_step),
                            DataType.S1615),
            NeuronParameter(self.exp_tc(self._machine_time_step),
                            DataType.S1615),
            NeuronParameter(self.one_over_tau_rc, DataType.S1615),
            NeuronParameter(self.refract_timer, DataType.UINT32),
            NeuronParameter(self.scaled_t_refract(), DataType.UINT32)
        ]
