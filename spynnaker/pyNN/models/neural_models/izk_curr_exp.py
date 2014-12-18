from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.utilities import constants
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_Izhikevich_vertex \
    import AbstractIzhikevichVertex
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class IzhikevichCurrentExponentialPopulation(
        AbstractIzhikevichVertex, AbstractExponentialPopulationVertex,
        AbstractPopulationVertex):

    CORE_APP_IDENTIFIER = constants.IZK_CURRENT_EXP_CORE_APPLICATION_ID
    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, a=0.02, c=-65.0, b=0.2, d=2.0, i_offset=0,
                 u_init=-14.0, v_init=-70.0, tau_syn_E=5.0, tau_syn_I=5.0):

        # Instantiate the parent classes
        AbstractExponentialPopulationVertex.__init__(
            self, n_neurons=n_neurons, tau_syn_E=tau_syn_E,
            tau_syn_I=tau_syn_I, machine_time_step=machine_time_step)
        AbstractIzhikevichVertex.__init__(self, n_neurons, a=a, c=c, b=b, d=d,
                                          i_offset=i_offset, u_init=u_init,
                                          v_init=v_init)
        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, n_params=10, label=label,
            binary="IZK_curr_exp.aplx", constraints=constraints,
            max_atoms_per_core=IzhikevichCurrentExponentialPopulation.
            _model_based_max_atoms_per_core,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma)
        self._executable_constant = \
            IzhikevichCurrentExponentialPopulation.CORE_APP_IDENTIFIER

    @property
    def model_name(self):
        return "IZK_curr_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IzhikevichCurrentExponentialPopulation.\
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
            NeuronParameter(self._a, DataType.S1615),
            NeuronParameter(self._b, DataType.S1615),
            NeuronParameter(self._c, DataType.S1615),
            NeuronParameter(self._d, DataType.S1615),
            NeuronParameter(self._v_init, DataType.S1615),
            NeuronParameter(self._u_init, DataType.S1615),
            NeuronParameter(self.ioffset(self._machine_time_step),
                    DataType.S1615),
            NeuronParameter(0, DataType.S1615)
        ]

    def is_population_vertex(self):
        return True

    def is_exp_vertex(self):
        return True

    def is_recordable(self):
        return True

    def is_izhikevich_vertex(self):
        return True
