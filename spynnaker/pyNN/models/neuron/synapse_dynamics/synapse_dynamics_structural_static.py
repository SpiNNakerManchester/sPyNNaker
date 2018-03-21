from six import itervalues
import numpy as np

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.synapse_dynamics import \
    AbstractSynapseDynamicsStructural
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    synapse_dynamics_structural_common import \
    SynapseDynamicsStructuralCommon as CommonSP
from .synapse_dynamics_static import SynapseDynamicsStatic


class SynapseDynamicsStructuralStatic(AbstractSynapseDynamicsStructural,
                                      SynapseDynamicsStatic):
    __slots__ = ["_common_sp"]

    def __init__(self, stdp_model=CommonSP.default_parameters['stdp_model'],
                 f_rew=CommonSP.default_parameters['f_rew'],
                 weight=CommonSP.default_parameters['weight'],
                 delay=CommonSP.default_parameters['delay'],
                 s_max=CommonSP.default_parameters['s_max'],
                 sigma_form_forward=CommonSP.default_parameters[
                     'sigma_form_forward'],
                 sigma_form_lateral=CommonSP.default_parameters[
                     'sigma_form_lateral'],
                 p_form_forward=CommonSP.default_parameters['p_form_forward'],
                 p_form_lateral=CommonSP.default_parameters['p_form_lateral'],
                 p_elim_dep=CommonSP.default_parameters['p_elim_dep'],
                 p_elim_pot=CommonSP.default_parameters['p_elim_pot'],
                 grid=CommonSP.default_parameters['grid'],
                 lateral_inhibition=CommonSP.default_parameters[
                     'lateral_inhibition'],
                 random_partner=CommonSP.default_parameters['random_partner'],
                 seed=None):
        if (stdp_model is not None and not isinstance(stdp_model,
                                                      SynapseDynamicsStatic)):
            raise TypeError("Using wrong StructuralMechanism. "
                            "You should be using StructuralMechanismSTDP. ")

        SynapseDynamicsStatic.__init__(self, pad_to_length=s_max)
        AbstractSynapseDynamicsStructural.__init__(self)

        self._common_sp = CommonSP(
            stdp_model=self, f_rew=f_rew, weight=weight,
            delay=delay, s_max=s_max,
            sigma_form_forward=sigma_form_forward,
            sigma_form_lateral=sigma_form_lateral,
            p_form_forward=p_form_forward,
            p_form_lateral=p_form_lateral,
            p_elim_dep=p_elim_dep,
            p_elim_pot=p_elim_pot, grid=grid,
            lateral_inhibition=lateral_inhibition,
            random_partner=random_partner, seed=seed)

    @overrides(SynapseDynamicsStatic.write_parameters,
               additional_arguments={"application_graph", "machine_graph",
                                     "app_vertex",
                                     "post_slice", "machine_vertex",
                                     "graph_mapper", "routing_info"})
    def write_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info):
        super(SynapseDynamicsStructuralStatic, self).write_parameters(
            spec, region, machine_time_step, weight_scales)

        self._common_sp.write_parameters(
            spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info)

    @overrides(SynapseDynamicsStatic.is_same_as)
    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, SynapseDynamicsStructuralStatic):
            return False
        return self._common_sp.is_same_as(synapse_dynamics)

    @overrides(SynapseDynamicsStatic.are_weights_signed)
    def are_weights_signed(self):
        return super(SynapseDynamicsStructuralStatic,
                     self).are_weights_signed()

    @overrides(SynapseDynamicsStatic.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        name = super(SynapseDynamicsStructuralStatic,
                     self).get_vertex_executable_suffix()
        name += self._common_sp.get_vertex_executable_suffix()
        return name

    @overrides(SynapseDynamicsStatic.get_parameters_sdram_usage_in_bytes,
               additional_arguments={"in_edges"})
    def get_parameters_sdram_usage_in_bytes(self, n_neurons,
                                            n_synapse_types, in_edges):
        initial_size = \
            super(SynapseDynamicsStructuralStatic, self). \
                get_parameters_sdram_usage_in_bytes(
                n_neurons, n_synapse_types)
        initial_size += \
            self._common_sp.get_parameters_sdram_usage_in_bytes(
                n_neurons, n_synapse_types, in_edges)
        return initial_size

    @overrides(SynapseDynamicsStatic.get_n_words_for_static_connections)
    def get_n_words_for_static_connections(self, n_connections):
        value = super(SynapseDynamicsStructuralStatic,
                      self).get_n_words_for_static_connections(n_connections)
        self._common_sp.n_words_for_static_connections(value)
        return value

    @overrides(SynapseDynamicsStatic.get_static_synaptic_data,
               additional_arguments={"app_edge", "machine_edge"})
    def get_static_synaptic_data(self, connections, connection_row_indices,
                                 n_rows, post_vertex_slice,
                                 n_synapse_types, app_edge, machine_edge):
        self._common_sp.synaptic_data_update(
            connections, post_vertex_slice,
            app_edge, machine_edge)
        return super(SynapseDynamicsStructuralStatic,
                     self).get_static_synaptic_data(
            connections, connection_row_indices, n_rows, post_vertex_slice,
            n_synapse_types)

    @overrides(SynapseDynamicsStatic.get_n_static_words_per_row)
    def get_n_static_words_per_row(self, ff_size):

        return super(SynapseDynamicsStructuralStatic,
                     self).get_n_static_words_per_row(ff_size)

    @overrides(SynapseDynamicsStatic.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, ff_size):
        return super(SynapseDynamicsStructuralStatic,
                     self).get_n_synapses_in_rows(ff_size)

    @overrides(SynapseDynamicsStatic.read_static_synaptic_data)
    def read_static_synaptic_data(self, post_vertex_slice, n_synapse_types,
                                  ff_size, ff_data):
        return super(SynapseDynamicsStructuralStatic,
                     self).read_static_synaptic_data(post_vertex_slice,
                                                     n_synapse_types, ff_size,
                                                     ff_data)

    @overrides(SynapseDynamicsStatic.get_parameter_names)
    def get_parameter_names(self):
        names = super(SynapseDynamicsStructuralStatic,
                      self).get_parameter_names()
        names.extend(self._common_sp.get_parameter_names())

        return names

    @overrides(SynapseDynamicsStatic.get_max_synapses)
    def get_max_synapses(self, n_words):
        return super(SynapseDynamicsStructuralStatic, self).get_max_synapses(
            n_words)
