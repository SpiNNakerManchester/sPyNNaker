from six import itervalues
import numpy as np
import collections

from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections import ProjectionMachineEdge
from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsStructuralCommon
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_synapse_dynamics_structural import \
    AbstractSynapseDynamicsStructural
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_static import SynapseDynamicsStatic
from spynnaker.pyNN.utilities import constants


class SynapseDynamicsStructuralSTDP(AbstractSynapseDynamicsStructural,
                                    SynapseDynamicsSTDP):

    def __init__(
            self,
            stdp_model=
            SynapseDynamicsStructuralCommon.default_parameters['stdp_model'],
            f_rew=SynapseDynamicsStructuralCommon.default_parameters['f_rew'],
            weight=SynapseDynamicsStructuralCommon.default_parameters['weight'],
            delay=SynapseDynamicsStructuralCommon.default_parameters['delay'],
            s_max=SynapseDynamicsStructuralCommon.default_parameters['s_max'],
            sigma_form_forward=SynapseDynamicsStructuralCommon.default_parameters['sigma_form_forward'],
            sigma_form_lateral=SynapseDynamicsStructuralCommon.default_parameters['sigma_form_lateral'],
            p_form_forward=SynapseDynamicsStructuralCommon.default_parameters['p_form_forward'],
            p_form_lateral=SynapseDynamicsStructuralCommon.default_parameters['p_form_lateral'],
            p_elim_dep=SynapseDynamicsStructuralCommon.default_parameters['p_elim_dep'],
            p_elim_pot=SynapseDynamicsStructuralCommon.default_parameters['p_elim_pot'],
            grid=SynapseDynamicsStructuralCommon.default_parameters['grid'],
            lateral_inhibition=SynapseDynamicsStructuralCommon.default_parameters['lateral_inhibition'],
            random_partner=SynapseDynamicsStructuralCommon.default_parameters['random_partner'],
            seed=None):
        if stdp_model is not None and \
                isinstance(stdp_model, SynapseDynamicsStatic):
            raise Exception("You fucked up.")

        SynapseDynamicsSTDP.__init__(
            self,
            timing_dependence=stdp_model.timing_dependence,
            weight_dependence=stdp_model.weight_dependence,
            dendritic_delay_fraction=stdp_model.dendritic_delay_fraction,
            pad_to_length=self._s_max)
        AbstractSynapseDynamicsStructural.__init__(self)
