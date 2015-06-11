"""
IzhikevichCurrentExponentialPopulation
"""
from spynnaker.pyNN.models.components.\
    inputs_components.current_component import CurrentComponent
from spynnaker.pyNN.models.components.neuron_components.\
    abstract_population_vertex import AbstractPopulationVertex
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.components.synapse_shape_components.\
    exponential_component import ExponentialComponent
from spynnaker.pyNN.models.components.model_components.izhikevich_component \
    import IzhikevichComponent
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter


class IzhikevichCurrentExponentialPopulation(
        CurrentComponent, IzhikevichComponent, ExponentialComponent,
        AbstractPopulationVertex):
    """
    IzhikevichCurrentExponentialPopulation
    """

    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_keys, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, a=0.02, c=-65.0, b=0.2, d=2.0, i_offset=0,
                 u_init=-14.0, v_init=-70.0, tau_syn_E=5.0, tau_syn_I=5.0):

        # Instantiate the parent classes
        ExponentialComponent.__init__(
            self, n_keys=n_keys, tau_syn_E=tau_syn_E,
            tau_syn_I=tau_syn_I, machine_time_step=machine_time_step)
        IzhikevichComponent.__init__(
            self, n_keys, a=a, c=c, b=b, d=d, i_offset=i_offset,
            u_init=u_init, v_init=v_init)
        AbstractPopulationVertex.__init__(
            self, n_keys=n_keys, n_params=10, label=label,
            binary="IZK_curr_exp.aplx", constraints=constraints,
            max_atoms_per_core=IzhikevichCurrentExponentialPopulation.
            _model_based_max_atoms_per_core,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma)

    @property
    def model_name(self):
        """
        human readable version of the model binary
        :return:
        """
        return "IZK_curr_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """
        helper method for setting the max atoms per core for a model
        :param new_value:
        :return:
        """
        IzhikevichCurrentExponentialPopulation.\
            _model_based_max_atoms_per_core = new_value

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the CPU requirements for a range of atoms
        :param vertex_slice: the slice of the partitionable vertex to which
        to figure the cpu usage of
        :param graph: the partitionable graph
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
        """
        helper emthod for isinstance
        :return:
        """
        return True

    def is_exp_vertex(self):
        """
        helper emthod for isinstance
        :return:
        """
        return True

    def is_recordable(self):
        """
        helper emthod for isinstance
        :return:
        """
        return True

    def is_izhikevich_vertex(self):
        """
        helper emthod for isinstance
        :return:
        """
        return True

    def is_current_component(self):
        """
        helper emthod for is instance
        :return:
        """
        return True
