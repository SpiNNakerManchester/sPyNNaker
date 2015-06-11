"""
IFCurrentDualExponentialPopulation
"""
from spynnaker.pyNN.models.components.inputs_components.\
    current_component import CurrentComponent
from spynnaker.pyNN.models.components.neuron_components.\
    abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.components.synapse_shape_components.\
    dual_exponential_component import DualExponentialComponent
from spynnaker.pyNN.models.components.model_components.\
    integrate_and_fire_component import IntegrateAndFireComponent
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter

from data_specification.enums.data_type import DataType


class IFCurrentDualExponentialPopulation(
        DualExponentialComponent, IntegrateAndFireComponent, CurrentComponent,
        AbstractPopulationVertex):
    """
    IFCurrentDualExponentialPopulation
    """

    _model_based_max_atoms_per_core = 256

    # noinspection PyPep8Naming
    def __init__(self, n_keys, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
                 v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0,
                 tau_refrac=0.1, i_offset=0, v_init=None):

        # Instantiate the parent classes
        CurrentComponent.__init__(self)
        DualExponentialComponent.__init__(
            self, n_keys=n_keys, tau_syn_E=tau_syn_E,
            tau_syn_E2=tau_syn_E2, tau_syn_I=tau_syn_I,
            machine_time_step=machine_time_step)
        IntegrateAndFireComponent.__init__(
            self, atoms=n_keys, cm=cm, tau_m=tau_m, i_offset=i_offset,
            v_init=v_init, v_reset=v_reset, v_rest=v_rest, v_thresh=v_thresh,
            tau_refrac=tau_refrac)
        AbstractPopulationVertex.__init__(
            self, n_keys=n_keys, n_params=10, label=label,
            binary="IF_curr_exp_dual.aplx", constraints=constraints,
            max_atoms_per_core=(IFCurrentDualExponentialPopulation
                                ._model_based_max_atoms_per_core),
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma)

    @property
    def model_name(self):
        """
        human readable name for the model
        :return:
        """
        return "IF_curr_dual_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """
        helper method for the max atoms per core for a model
        :param new_value:
        :return:
        """
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
            NeuronParameter(self._one_over_tau_rc, DataType.S1615),
            NeuronParameter(self._refract_timer, DataType.UINT32),
            # t refact used to be a uint32 but was changed to int32 to avoid
            # clash of c and python variable typing.
            NeuronParameter(self._scaled_t_refract(), DataType.INT32)
        ]

    def is_population_vertex(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def is_duel_exponential_vertex(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def is_integrate_and_fire_vertex(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def is_recordable(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def is_current_component(self):
        """
        helper method for isinstance
        :return:
        """
        return True
