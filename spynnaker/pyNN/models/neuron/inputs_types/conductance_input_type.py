"""
AbstractConductanceVertex
"""

from spynnaker.pyNN.models.neuron.inputs_components.\
    abstract_input_type_component import AbstractInputTypeComponent
from spynnaker.pyNN.utilities import utility_calls


class ConductanceInputType(AbstractInputTypeComponent):
    """ Parameters for the conductance input type
    """

    # noinspection PyPep8Naming
    def __init__(self, n_keys, e_rev_E, e_rev_I):
        AbstractInputTypeComponent.__init__(self)

        self._e_rev_E = utility_calls.convert_param_to_numpy(e_rev_E,
                                                             n_keys)
        self._e_rev_I = utility_calls.convert_param_to_numpy(e_rev_I,
                                                             n_keys)

    # noinspection PyPep8Naming
    @property
    def e_rev_E(self):
        """
        property for the e_rev_e
        :return:
        """
        return self._e_rev_E

    # noinspection PyPep8Naming
    @e_rev_E.setter
    def e_rev_E(self, new_value):
        """
        setter for the e_rev_E property
        :param new_value:
        :return:
        """
        self._e_rev_E = new_value

    # noinspection PyPep8Naming
    @property
    def e_rev_I(self):
        """
        e_rev_i property
        :return:
        """
        return self._e_rev_I

    # noinspection PyPep8Naming
    @e_rev_I.setter
    def e_rev_I(self, new_value):
        """
        setter for the e_rev_i property
        :param new_value:
        :return:
        """
        self._e_rev_I = new_value

    def get_n_input_parameters(self):
        return 2

    def get_input_component_source_name(self):
        # TODO replace with header file name once this has been refactored
        return ""

    def get_input_weight_scale(self):
        return 1024.0
