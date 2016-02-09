# spynnaker imports
from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex

# spinn front end common imports
from spinn_front_end_common.utilities import constants

# general imports
import os
import hashlib


class FAKEIFCurrExp(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input but which runs for much much longer than it really should
    """

    _model_based_max_atoms_per_core = 255

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
        'v_thresh': -50.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
        'tau_refrac': 0.1, 'i_offset': 0}

    def __init__(
            self, n_neurons, machine_time_step, timescale_factor,
            spikes_per_second=None, ring_buffer_sigma=None, constraints=None,
            label=None,
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],
            tau_syn_E=default_parameters['tau_syn_E'],
            tau_syn_I=default_parameters['tau_syn_I'],
            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'], v_init=None):

        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, machine_time_step, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            n_neurons, machine_time_step, tau_syn_E, tau_syn_I)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_exp.aplx", label=label,
            max_atoms_per_core=FAKEIFCurrExp._model_based_max_atoms_per_core,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            model_name="IF_curr_exp", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        FAKEIFCurrExp._model_based_max_atoms_per_core = new_value

    def _write_basic_setup_info(self, spec, region_id):

        # Hash application title
        application_name = os.path.splitext(self.get_binary_file_name())[0]

        # Get first 32-bits of the md5 hash of the application name
        application_name_hash = hashlib.md5(application_name).hexdigest()[:8]

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=region_id)
        spec.write_value(data=int(application_name_hash, 16))
        spec.write_value(data=self._machine_time_step * self._timescale_factor)

        # check for infinite runs and add data as required
        if self._no_machine_time_steps is None:
            spec.write_value(data=1)
            spec.write_value(data=0)
        else:
            spec.write_value(data=0)
            spec.write_value(data=self._no_machine_time_steps)

        # add SDP port number for receiving synchronisations and new run times
        spec.write_value(
            data=constants.SDP_PORTS.RUNNING_COMMAND_SDP_PORT.value)

    def set_no_machine_time_steps(self, new_no_machine_time_steps):
        """

        :param new_no_machine_time_steps:
        :return:
        """
        self._no_machine_time_steps = new_no_machine_time_steps * 10