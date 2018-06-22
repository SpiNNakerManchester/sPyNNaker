from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from spynnaker.pyNN.utilities import utility_calls
from pacman.executor.injection_decorator import inject_items

DU_TH = "du_th"
TAU_TH = "tau_th"
V_THRESH = "v_thresh"

UNITS = {
    DU_TH: "mV",
    TAU_TH: "ms",
    V_THRESH: "mV"
}


class ThresholdTypeMaassStochastic(AbstractThresholdType):
    """ A stochastic threshold
    """
    __slots__ = [
        "_du_th",
        "_tau_th",
        "_v_thresh"]

    def __init__(self, du_th, tau_th, v_thresh):
        self._du_th = du_th
        self._tau_th = tau_th
        self._v_thresh = v_thresh

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 30 * n_neurons

    @overrides(AbstractThresholdType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 4 parameters per neuron (4 bytes each)
        return (4 * 4 * n_neurons)

    @overrides(AbstractThresholdType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 4 parameters per neuron (4 bytes each)
        return (4 * 4 * n_neurons)

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(DU_TH, self._du_th)
        parameters.set_value(TAU_TH, self._tau_th)
        parameters.set_value(V_THRESH, self._v_thresh)

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractThresholdType.get_data,
               additional_arguments={'machine_time_step'})
    def get_data(
            self, parameters, state_variables, vertex_slice,
            machine_time_step):

        # Add the rest of the data
        items = [
            (parameters[DU_TH].apply_operation(lambda x: 1.0 / x),
             DataType.S1615),
            (parameters[TAU_TH].apply_operation(lambda x: 1.0 / x),
             DataType.S1615),
            (parameters[V_THRESH], DataType.S1615),
            (float(machine_time_step) / 10000.0, DataType.S1615)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractThresholdType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615 * 4]
        offset, (_du_th, _tau_th, _v_thresh, _time_step_ms_div_10) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        return offset

    @property
    def v_thresh(self):
        return self._v_thresh

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._v_thresh = v_thresh

    @property
    def du_th(self):
        return self._du_th

    @du_th.setter
    def du_th(self, du_th):
        self._du_th = du_th

    @property
    def tau_th(self):
        return self._tau_th

    @tau_th.setter
    def tau_th(self, tau_th):
        self._tau_th = tau_th
