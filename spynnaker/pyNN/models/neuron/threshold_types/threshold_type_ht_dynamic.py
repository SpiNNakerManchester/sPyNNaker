from pacman.model.decorators import overrides
from .abstract_threshold_type import AbstractThresholdType
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items

import numpy

V_THRESH = "v_thresh"
V_THRESH_RESTING = "v_thresh_resting"
V_THRESH_TAU = "v_thresh_tau"
V_THRESH_NA_REVERSAL = "v_thresh_Na_reversal"

UNITS = {
    V_THRESH: "mV",
    V_THRESH_RESTING: "mV",
    V_THRESH_TAU: "ms",
    V_THRESH_NA_REVERSAL: "mV"
    }


class ThresholdTypeHTDynamic(AbstractThresholdType):

    """ A threshold which increases when the neuron spikes, and decays
        exponentially back to baseline with time
    """

    __slots__ = [
        "_v_thresh",
        "_v_thresh_resting",
        "_v_thresh_tau",
        "_v_thresh_Na_reversal"
        ]

    def __init__(self, v_thresh_init,
                 v_thresh_resting, v_thresh_tau, v_thresh_Na_reversal):
        super(ThresholdTypeHTDynamic, self).__init__([
            DataType.S1615,    # v_thresh
            DataType.S1615,    # v_thresh_resting
            DataType.S1615,    # v_thresh_tau
            DataType.S1615,    # v_thresh_Na_reversal
            ])

        self._v_thresh = v_thresh_init
        self._v_thresh_resting = v_thresh_resting
        self._v_thresh_tau = v_thresh_tau
        self._v_thresh_Na_reversal = v_thresh_Na_reversal

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # Just a comparison, but 2 just in case!
        return 2 * n_neurons

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_THRESH_RESTING] = self._v_thresh_resting
        parameters[V_THRESH_TAU] = self._v_thresh_tau
        parameters[V_THRESH_NA_REVERSAL] = self._v_thresh_Na_reversal

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V_THRESH] = self._v_thresh

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractThresholdType.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        tsfloat = float(ts) / 1000.0
        decay = lambda x: numpy.exp(-tsfloat / x)  # noqa E731

        # Add the rest of the data
        return [
            state_variables[V_THRESH],
            parameters[V_THRESH_RESTING],
            parameters[V_THRESH_TAU].apply_operation(decay),
            parameters[V_THRESH_NA_REVERSAL]
            ]

    @overrides(AbstractThresholdType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_v_thresh, _v_thresh_resting, _v_thresh_tau,
                                    _v_thresh_Na_reversal) = values

        state_variables[V_THRESH] = _v_thresh

    @property
    def v_thresh(self):
        return self._v_thresh

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._v_thresh = v_thresh

    @property
    def v_thresh_resting(self):
        return self._v_thresh_resting

    @v_thresh_resting.setter
    def v_thresh_resting(self, v_thresh_resting):
        self._v_thresh_resting = v_thresh_resting

    @property
    def v_thresh_tau(self):
        return self._v_thresh_tau

    @v_thresh_tau.setter
    def v_thresh_tau(self, v_thresh_tau):
        self._v_thresh_tau = v_thresh_tau

    @property
    def v_thresh_Na_reversal(self):
        return self._v_thresh_Na_reversal

    @v_thresh_Na_reversal.setter
    def v_thresh_Na_reversal(self, v_thresh_Na_reversal):
        self._v_thresh_Na_reversal = v_thresh_Na_reversal
