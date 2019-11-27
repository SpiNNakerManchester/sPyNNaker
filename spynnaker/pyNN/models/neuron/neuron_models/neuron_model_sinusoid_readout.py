import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel

MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"
# MEAN_ISI_TICKS = "mean_isi_ticks"
# TIME_TO_SPIKE_TICKS = "time_to_spike_ticks"
# SEED1 = "seed1"
# SEED2 = "seed2"
# SEED3 = "seed3"
# SEED4 = "seed4"
# TICKS_PER_SECOND = "ticks_per_second"
# TIME_SINCE_LAST_SPIKE = "time_since_last_spike"
# RATE_AT_LAST_SETTING = "rate_at_last_setting"
# RATE_UPDATE_THRESHOLD = "rate_update_threshold"
TARGET_DATA = "target_data"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms'
}


class NeuronModelLeakyIntegrateAndFireSinusoidReadout(AbstractNeuronModel):
    __slots__ = [
        "_v_init",
        "_v_rest",
        "_tau_m",
        "_cm",
        "_i_offset",
        "_v_reset",
        "_tau_refrac",
        "_mean_isi_ticks",
        "_time_to_spike_ticks",
        "_time_since_last_spike",
        "_rate_at_last_setting",
        "_rate_update_threshold",
        "_target_data"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
#             mean_isi_ticks, time_to_spike_ticks, rate_update_threshold,
            target_data):

        global_data_types=[
#                     DataType.UINT32,  # MARS KISS seed
#                     DataType.UINT32,  # MARS KISS seed
#                     DataType.UINT32,  # MARS KISS seed
#                     DataType.UINT32,  # MARS KISS seed
#                     DataType.S1615,    # ticks_per_second
                    DataType.S1615    # global mem pot
                    ]
        global_data_types.extend([DataType.S1615 for i in range(1024)])


        super(NeuronModelLeakyIntegrateAndFireSinusoidReadout, self).__init__(
            data_types= [
                DataType.S1615,   #  v
                DataType.S1615,   #  v_rest
                DataType.S1615,   #  r_membrane (= tau_m / cm)
                DataType.S1615,   #  exp_tc (= e^(-ts / tau_m))
                DataType.S1615,   #  i_offset
                DataType.INT32,   #  count_refrac
                DataType.S1615,   #  v_reset
                DataType.INT32,   #  tau_refrac
                #### Poisson Compartment Params ####
#                 DataType.S1615,   #  REAL mean_isi_ticks
#                 DataType.S1615,   #  REAL time_to_spike_ticks
#                 DataType.INT32,    #  int32_t time_since_last_spike s
#                 DataType.S1615,   #  REAL rate_at_last_setting; s
#                 DataType.S1615   #  REAL rate_update_threshold; p
                ],

            global_data_types=global_data_types
            )

        if v_init is None:
            v_init = v_rest

        self._v_init = v_init
        self._v_rest = v_rest
        self._tau_m = tau_m
        self._cm = cm
        self._i_offset = i_offset
        self._v_reset = v_reset
        self._tau_refrac = tau_refrac
#         self._mean_isi_ticks = mean_isi_ticks
#         self._time_to_spike_ticks = time_to_spike_ticks
#         self._time_since_last_spike = 0 # this should be initialised to zero - we know nothing about before the simulation
#         self._rate_at_last_setting = 0
#         self._rate_update_threshold = 2
        self._target_data = target_data

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self._v_rest
        parameters[TAU_M] = self._tau_m
        parameters[CM] = self._cm
        parameters[I_OFFSET] = self._i_offset
        parameters[V_RESET] = self._v_reset
        parameters[TAU_REFRAC] = self._tau_refrac
#         parameters[SEED1] = 10065
#         parameters[SEED2] = 232
#         parameters[SEED3] = 3634
#         parameters[SEED4] = 4877
        parameters[TARGET_DATA] = 0.0

#         parameters[TICKS_PER_SECOND] = 0 # set in get_valuers()
#         parameters[RATE_UPDATE_THRESHOLD] = self._rate_update_threshold
#         parameters[TARGET_DATA] = self._target_data

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self._v_init
        state_variables[COUNT_REFRAC] = 0
#         state_variables[MEAN_ISI_TICKS] = self._mean_isi_ticks
#         state_variables[TIME_TO_SPIKE_TICKS] = self._time_to_spike_ticks # could eventually be set from membrane potential
#         state_variables[TIME_SINCE_LAST_SPIKE] = self._time_since_last_spike
#         state_variables[RATE_AT_LAST_SETTING] = self._rate_at_last_setting


    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [state_variables[V],
                parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),
#                 state_variables[MEAN_ISI_TICKS],
#                 state_variables[TIME_TO_SPIKE_TICKS],
#                 state_variables[TIME_SINCE_LAST_SPIKE],
#                 state_variables[RATE_AT_LAST_SETTING],
#                 parameters[RATE_UPDATE_THRESHOLD]
                ]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac,
#          mean_isi_ticks, time_to_spike_ticks, time_since_last_spike,
#          rate_at_last_setting, _rate_update_threshold
#          _seed1, _seed2, _seed3, _seed4, _ticks_per_second
         ) = values

        # Copy the changed data only
        state_variables[V] = v
#         state_variables[COUNT_REFRAC] = count_refrac
#         state_variables[MEAN_ISI_TICKS] = mean_isi_ticks
#         state_variables[TIME_TO_SPIKE_TICKS] = time_to_spike_ticks
#         state_variable[TIME_SINCE_LAST_SPIKE] = time_since_last_spike
#         state_variabels[RATE_AT_LAST_SETTING] = rate_at_last_setting

    # Global params
    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'machine_time_step'})
    def get_global_values(self, machine_time_step):
        vals = [
#                 1, # seed 1
#                 2, # seed 2
#                 3, # seed 3
#                 4, # seed 4
#                 MICROSECONDS_PER_SECOND / float(machine_time_step), # ticks_per_second
                0.0, # set to 0, as will be set in first timestep of model anyway (membrane potential)
                ]

#         target_data = []
#
#         for i in range(1024):
#             target_data.append(
# #                 4
#                 5 + 2 * numpy.sin(2 * i * 2* numpy.pi / 1024) \
#                     + 5 * numpy.sin((4 * i * 2* numpy.pi / 1024))
#                 )
        vals.extend(self._target_data)
        return vals

    @property
    def target_data(self):
        return self._target_data

    @target_data.setter
    def target_data(self, target_data):
        self._target_data = target_data

    @property
    def v_init(self):
        return self._v

    @v_init.setter
    def v_init(self, v_init):
        self._v = v_init

    @property
    def v_rest(self):
        return self._v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self._v_rest = v_rest

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self._tau_m = tau_m

    @property
    def cm(self):
        return self._cm

    @cm.setter
    def cm(self, cm):
        self._cm = cm

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = i_offset

    @property
    def v_reset(self):
        return self._v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self._v_reset = v_reset

    @property
    def tau_refrac(self):
        return self._tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._tau_refrac = tau_refrac

#     @property
#     def mean_isi_ticks(self):
#         return self._mean_isi_ticks
#
#     @mean_isi_ticks.setter
#     def mean_isi_ticks(self, new_mean_isi_ticks):
#         self._mean_isi_ticks = new_mean_isi_ticks
#
#     @property
#     def time_to_spike_ticks(self):
#         return self._time_to_spike_ticks
#
#     @mean_isi_ticks.setter
#     def time_to_spike_ticks(self, new_time_to_spike_ticks):
#         self._time_to_spike_ticks = new_time_to_spike_ticks