import numpy as np

from spynnaker.pyNN.models.neuron.synapse_dynamics \
    .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics


class SynapseDynamicsStructural(AbstractPlasticSynapseDynamics):
    def __init__(self, f_rew=10 ** 4, s_max=32,
                 sigma_form_forward=2.5, sigma_form_lateral=1,
                 p_form_forward=0.16, p_form_lateral=1,
                 p_elim_dep=0.0245, p_elim_pot=1.36 * np.e ** -4, distance_type='euclidian'):
        super(SynapseDynamicsStructural, self).__init__()
        self._f_rew = f_rew
        self._s_max = s_max
        self._sigma_form_forward = sigma_form_forward
        self._sigma_form_lateral = sigma_form_lateral
        self._p_form_forward = p_form_forward
        self._p_form_lateral = p_form_lateral
        self._p_elim_dep = p_elim_dep
        self._p_elim_pot = p_elim_pot
        self._distance_type = distance_type

    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        pass

    def get_vertex_executable_suffix(self):
        pass

    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, SynapseDynamicsStructural):
            return False
        return (
            self._f_rew == synapse_dynamics._f_rew and
            self._s_max == synapse_dynamics._s_max and
            np.isclose(self._sigma_form_forward, synapse_dynamics._sigma_form_forward) and
            np.isclose(self._sigma_form_lateral, synapse_dynamics._sigma_form_lateral) and
            np.isclose(self._p_form_forward, synapse_dynamics._p_form_forward) and
            np.isclose(self._p_form_lateral, synapse_dynamics._p_form_lateral) and
            np.isclose(self._p_elim_dep, synapse_dynamics._p_elim_dep) and
            np.isclose(self._p_elim_pot, synapse_dynamics._p_elim_pot) and
            self._distance_type == synapse_dynamics._distance_type
        )

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        pass

    def are_weights_signed(self):
        pass

    def read_plastic_synaptic_data(self, post_vertex_slice, n_synapse_types, pp_size, pp_data, fp_size, fp_data):
        pass

    def get_n_synapses_in_rows(self, pp_size, fp_size):
        pass

    def get_n_fixed_plastic_words_per_row(self, fp_size):
        pass

    def get_n_plastic_plastic_words_per_row(self, pp_size):
        pass

    def get_plastic_synaptic_data(self, connections, connection_row_indices, n_rows, post_vertex_slice,
                                  n_synapse_types):
        pass

    def get_n_words_for_plastic_connections(self, n_connections):
        pass
