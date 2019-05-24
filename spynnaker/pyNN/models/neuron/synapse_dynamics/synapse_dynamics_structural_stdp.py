from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural, SynapseDynamicsSTDP)
from .synapse_dynamics_structural_common import (
    SynapseDynamicsStructuralCommon as
    CommonSP)


class SynapseDynamicsStructuralSTDP(AbstractSynapseDynamicsStructural,
                                    SynapseDynamicsSTDP):
    """ Class that enables synaptic rewiring. It acts as a wrapper
        around SynapseDynamicsSTDP.
        This means rewiring can operate in parallel with these
        types of synapses.

        Written by Petrut Bogdan.

        Example usage to allow rewiring in parallel with STDP::

            stdp_model = sim.STDPMechanism(...)

            structure_model_with_stdp = sim.StructuralMechanismSTDP(
                stdp_model=stdp_model,
                weight=0,
                s_max=32,
                grid=[np.sqrt(pop_size), np.sqrt(pop_size)],
                random_partner=True,
                f_rew=10 ** 4,  # Hz
                sigma_form_forward=1.,
                delay=10
            )
            plastic_projection = sim.Projection(
                ...,
                synapse_dynamics=sim.SynapseDynamics(
                    slow=structure_model_with_stdp
                )
            )


    :param f_rew: Frequency of rewiring (Hz). How many rewiring attempts will\
        be done per second.
    :type f_rew: int
    :param weight: Initial weight assigned to a newly formed connection
    :type weight: float
    :param delay: Delay assigned to a newly formed connection
    :type delay: int
    :param s_max: Maximum fan-in per target layer neuron
    :type s_max: int
    :param sigma_form_forward: Spread of feed-forward formation receptive field
    :type sigma_form_forward: float
    :param sigma_form_lateral: Spread of lateral formation receptive field
    :type sigma_form_lateral: float
    :param p_form_forward: Peak probability for feed-forward formation
    :type p_form_forward: float
    :param p_form_lateral: Peak probability for lateral formation
    :type p_form_lateral: float
    :param p_elim_pot: Probability of elimination of a potentiated synapse
    :type p_elim_pot: float
    :param p_elim_dep: Probability of elimination of a depressed synapse
    :type p_elim_dep: float
    :param grid: Grid shape
    :type grid: 2d int array
    :param lateral_inhibition: Flag whether to mark synapses formed within a\
        layer as inhibitory or excitatory
    :type lateral_inhibition: bool
    :param random_partner: Flag whether to randomly select pre-synaptic\
        partner for formation
    :type random_partner: bool
    :param seed: seed the random number generators
    :type seed: int
    """
    __slots__ = ["__common_sp"]

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
        if (stdp_model is not None
                and not isinstance(stdp_model, SynapseDynamicsSTDP)):
            raise TypeError("Using wrong StructuralMechanism. "
                            "You should be using StructuralMechanismStatic. ")
        SynapseDynamicsSTDP.__init__(self, stdp_model.timing_dependence,
                                     stdp_model.weight_dependence,
                                     None,
                                     stdp_model.dendritic_delay_fraction,
                                     pad_to_length=s_max)
        AbstractSynapseDynamicsStructural.__init__(self)
        self.__common_sp = CommonSP(
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

    @overrides(SynapseDynamicsSTDP.write_parameters,
               additional_arguments={"application_graph", "machine_graph",
                                     "app_vertex",
                                     "post_slice", "machine_vertex",
                                     "graph_mapper", "routing_info"})
    def write_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info):
        super(SynapseDynamicsStructuralSTDP, self).write_parameters(
            spec, region, machine_time_step, weight_scales)
        self.__common_sp.write_parameters(
            spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info)

    @overrides(SynapseDynamicsSTDP.is_same_as)
    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, SynapseDynamicsStructuralSTDP):
            return False
        return self.__common_sp.is_same_as(synapse_dynamics)

    @overrides(SynapseDynamicsSTDP.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        name = super(SynapseDynamicsStructuralSTDP,
                     self).get_vertex_executable_suffix()
        name += self.__common_sp.get_vertex_executable_suffix()
        return name

    @overrides(SynapseDynamicsSTDP.get_parameters_sdram_usage_in_bytes,
               additional_arguments={"in_edges"})
    def get_parameters_sdram_usage_in_bytes(self, n_neurons,
                                            n_synapse_types, in_edges):
        initial_size = super(SynapseDynamicsStructuralSTDP, self). \
            get_parameters_sdram_usage_in_bytes(n_neurons, n_synapse_types)
        initial_size += self.__common_sp.get_parameters_sdram_usage_in_bytes(
            n_neurons, n_synapse_types, in_edges)
        return initial_size

    @overrides(SynapseDynamicsSTDP.get_n_words_for_plastic_connections)
    def get_n_words_for_plastic_connections(self, n_connections):
        value = super(SynapseDynamicsStructuralSTDP,
                      self).get_n_words_for_plastic_connections(n_connections)
        self.__common_sp.n_words_for_plastic_connections(value)
        return value

    @overrides(SynapseDynamicsSTDP.get_plastic_synaptic_data,
               additional_arguments={"app_edge", "machine_edge"})
    def get_plastic_synaptic_data(self, connections, connection_row_indices,
                                  n_rows, post_vertex_slice,
                                  n_synapse_types, app_edge, machine_edge):
        self.__common_sp.synaptic_data_update(
            connections, post_vertex_slice, app_edge, machine_edge)
        return super(SynapseDynamicsStructuralSTDP,
                     self).get_plastic_synaptic_data(
            connections, connection_row_indices, n_rows, post_vertex_slice,
            n_synapse_types)

    @overrides(SynapseDynamicsSTDP.get_parameter_names)
    def get_parameter_names(self):
        names = super(SynapseDynamicsStructuralSTDP,
                      self).get_parameter_names()
        names.extend(self.__common_sp.get_parameter_names())
        return names
