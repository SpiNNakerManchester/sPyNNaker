from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from .abstract_input_type import AbstractInputType


AMPA_REV_E = "ampa_rev_E"
NMDA_REV_E = "nmda_rev_E"
GABA_A_REV_E = "gaba_a_rev_E"
GABA_B_REV_E = "gaba_b_rev_E"


UNITS = {
    AMPA_REV_E: "mV",
    NMDA_REV_E: "mV",
    GABA_A_REV_E: "mV",
    GABA_B_REV_E: "mV"
}


class InputTypeHTConductance(AbstractInputType):

    __slots__[
        "ampa_rev_E",
        "nmda_rev_E",
        "gaba_a_rev_E",
        "gaba_b_rev_E"
        ]

    def __init__(self, ampa_rev_E, nmda_rev_E, gaba_a_rev_E, gaba_b_rev_E):
        super(InputTypeConductance, self).__init__([
            DataType.S1615,   # ampa_rev_E
            DataType.S1615,   # nmda_rev_E
            DataType.S1615,   # gaba_a_rev_E
            DataType.S1615    # gaba_b_rev_E
            ])
        self._ampa_rev_E = ampa_rev_E
        self._nmda_rev_E = nmda_rev_E
        self._gaba_a_rev_E = gaba_a_rev_E
        self._gaba_b_rev_E = gaba_b_rev_E

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 10 * n_neurons

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[AMPA_REV_E] = self._ampa_rev_E
        parameters[NMDA_REV_E] = self._ampa_rev_E
        parameters[GABA_A_REV_E] = self._gaba_a_rev_E
        parameters[GABA_B_REV_E] = self._gaba_b_rev_E

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        return [
            parameters[AMPA_REV_E],
            parameters[NMDA_REV_E],
            parameters[GABA_A_REV_E],
            parameters[GABA_B_REV_E]
            ]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_ampa_rev_E, _nmda_rev_E, gaba_a_rev_E, _gaba_b_rev_E) = values


    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

    @property
    def ampa_rev_E(self):
        return self._ampa_rev_E

    @ampa_rev_E.setter
    def ampa_rev_E(self, ampa_rev_E):
        self._ampa_rev_E = ampa_rev_E

    @property
    def nmda_rev_E(self):
        return self._nmda_rev_E

    @nmda_rev_E.setter
    def nmda_rev_E(self, nmda_rev_E):
        self._nmda_rev_E = nmda_rev_E

    @property
    def gaba_a_rev_E(self):
        return self._gaba_a_rev_E

    @gaba_a_rev_E.setter
    def gaba_a_rev_E(self, gaba_a_rev_E):
        self._gaba_a_rev_E = gaba_a_rev_E

    @property
    def gaba_b_rev_E(self):
        return self._gaba_b_rev_E

    @gaba_b_rev_E.setter
    def gaba_b_rev_E(self, gaba_b_rev_E):
        self._gaba_b_rev_E = gaba_b_rev_E






