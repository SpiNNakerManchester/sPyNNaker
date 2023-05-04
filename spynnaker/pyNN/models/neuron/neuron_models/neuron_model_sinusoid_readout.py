import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

# constants
SYNAPSES_PER_NEURON = 250   # around 415 with only 3 in syn_state

# MICROSECONDS_PER_SECOND = 1000000.0
# MICROSECONDS_PER_MILLISECOND = 1000.0

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
# COUNT_REFRAC = "count_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"
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
# Learning signal
L = "learning_signal"
W_FB = "feedback_weight"
ETA = "eta"

# eprop synapse
DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
UPDATE_READY = "update_ready"

# UNITS = {
#     V: 'mV',
#     V_REST: 'mV',
#     TAU_M: 'ms',
#     CM: 'nF',
#     I_OFFSET: 'nA',
#     V_RESET: 'mV',
#     TAU_REFRAC: 'ms'
# }


class NeuronModelLeakyIntegrateAndFireSinusoidReadout(AbstractStandardNeuronComponent):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",

        "__target_data",

        # learning signal
        "__l",
        "__w_fb",
        "__eta",
        "__update_ready"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
#             mean_isi_ticks, time_to_spike_ticks, rate_update_threshold,
            target_data,
            l,
            w_fb,
            eta,
            update_ready):

        struct_neuron_vals = [
            (DataType.S1615, V),  # v
            (DataType.S1615, V_REST), # v_rest
            (DataType.S1615, CM), # r_membrane (= tau_m / cm)
            (DataType.S1615, TAU_M),  # exp_tc (= e^(-ts / tau_m))
            (DataType.S1615, I_OFFSET),  # i_offset
            (DataType.S1615, V_RESET),  # v_reset
            (DataType.S1615, TAU_REFRAC), # tau_refrac
            (DataType.INT32, REFRACT_TIMER),  # count_refrac
            (DataType.S1615, TIMESTEP),  # timestep
            # Learning signal
            (DataType.S1615, L),  # L
            (DataType.S1615, W_FB)  # w_fb
        ]

        # former global parameters
        for n in range(1024):
            struct_neuron_vals.extend(
                [(DataType.S1615, TARGET_DATA+str(n))])
        struct_neuron_vals.extend([(DataType.S1615, ETA)])

        # Synapse states - always initialise to zero
        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                # eprop_syn_state
                [(DataType.S1615, DELTA_W+str(n)), # delta_w
                 (DataType.S1615, Z_BAR_OLD+str(n)), # z_bar_old
                 (DataType.S1615, Z_BAR+str(n)), # z_bar
                 (DataType.UINT32, UPDATE_READY+str(n))]) # update_ready

        super().__init__(
            [Struct(struct_neuron_vals)],
            {V: 'mV', V_REST: 'mV', TAU_M: 'ms', CM: 'nF', I_OFFSET: 'nA',
             V_RESET: 'mV', TAU_REFRAC: 'ms'})

        if v_init is None:
            v_init = v_rest

        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac

        self.__target_data = target_data

        # learning signal
        self.__l = l
        self.__w_fb = w_fb

        self.__eta = eta

        self.__update_ready = update_ready

    # @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    # def get_n_cpu_cycles(self, n_neurons):
    #     # A bit of a guess
    #     return 100 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

        # learning params
        parameters[W_FB] = self.__w_fb

        # Target data (formerly global data)
        for n in range(1024):
            parameters[TARGET_DATA+str(n)] = self.__target_data[n]

        parameters[ETA] = self.__eta


    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0

        # learning params
        state_variables[L] = self.__l

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self.__update_ready


    # @overrides(AbstractNeuronModel.get_units)
    # def get_units(self, variable):
    #     return UNITS[variable]
    #
    # @overrides(AbstractNeuronModel.has_variable)
    # def has_variable(self, variable):
    #     return variable in UNITS
    #
    # @inject_items({"ts": "MachineTimeStep"})
    # @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    # def get_values(self, parameters, state_variables, vertex_slice, ts):
    #
    #     # Add the rest of the data
    #     values = [state_variables[V],
    #             parameters[V_REST],
    #             parameters[TAU_M] / parameters[CM],
    #             parameters[TAU_M].apply_operation(
    #                 operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
    #             parameters[I_OFFSET], state_variables[COUNT_REFRAC],
    #             parameters[V_RESET],
    #             parameters[TAU_REFRAC].apply_operation(
    #                 operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),
    #
    #             state_variables[L],
    #             parameters[W_FB]
    #             ]
    #
    #     # create synaptic state - init all state to zero
    #     for n in range(SYNAPSES_PER_NEURON):
    #         eprop_syn_init = [0,    # delta w
    #                       0,    # z_bar_inp
    #                       0,#,    # z_bar
    #                       # 0,    # el_a
    #                       # 0]    # e_bar
    #                       self._update_ready, #int(numpy.random.rand()*1024)      # update_ready
    #                       ]
    #     # extend to appropriate fan-in
    #     values.extend(eprop_syn_init) # * SYNAPSES_PER_NEURON)
    #
    #     return values
    #
    # @overrides(AbstractNeuronModel.update_values)
    # def update_values(self, values, parameters, state_variables):
    #
    #     # Read the data
    #     (_v, _v_rest, _r_membrane, _exp_tc, _i_offset, _count_refrac,
    #     _v_reset, _tau_refrac,
    #     _l, _w_fb) = values  # Not sure this will work with the new array of synapse!!!
    #     # todo check alignment on this
    #
    #     # Copy the changed data only
    #     state_variables[V] = _v
    #
    #     state_variables[L] = _l
    #
    #
    # # Global params
    # @inject_items({"machine_time_step": "MachineTimeStep"})
    # @overrides(AbstractNeuronModel.get_global_values,
    #            additional_arguments={'machine_time_step'})
    # def get_global_values(self, machine_time_step):
    #     vals = []
    #
    #     vals.extend(self._target_data)
    #     vals.extend([self._eta])
    #     return vals

    @property
    def target_data(self):
        return self.__target_data

    @target_data.setter
    def target_data(self, target_data):
        self.__target_data = target_data

    @property
    def v_init(self):
        return self.__v_init

    @v_init.setter
    def v_init(self, v_init):
        self.__v_init = v_init

    @property
    def v_rest(self):
        return self.__v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self.__v_rest = v_rest

    @property
    def tau_m(self):
        return self.__tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self.__tau_m = tau_m

    @property
    def cm(self):
        return self.__cm

    @cm.setter
    def cm(self, cm):
        self.__cm = cm

    @property
    def i_offset(self):
        return self.__i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self.__i_offset = i_offset

    @property
    def v_reset(self):
        return self.__v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self.__v_reset = v_reset

    @property
    def tau_refrac(self):
        return self.__tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self.__tau_refrac = tau_refrac

    @property
    def w_fb(self):
        return self.__w_fb

    @w_fb.setter
    def w_fb(self, w_fb):
        self.__w_fb = w_fb
