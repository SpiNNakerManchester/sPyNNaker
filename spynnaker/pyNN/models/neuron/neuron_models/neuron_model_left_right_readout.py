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

# Learning signal
L = "learning_signal"
W_FB = "feedback_weight"
WINDOW_SIZE = "window_size"

MEAN_ISI_TICKS = "mean_isi_ticks"
TIME_TO_SPIKE_TICKS = "time_to_spike_ticks"
SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"
SEED4 = "seed4"
TICKS_PER_SECOND = "ticks_per_second"
TIME_SINCE_LAST_SPIKE = "time_since_last_spike"
RATE_AT_LAST_SETTING = "rate_at_last_setting"
# RATE_UPDATE_THRESHOLD = "rate_update_threshold"
# PROB_COMMAND = "prob_command"
MEAN_L = "mean_l"
MEAN_R = "mean_r"
RATE_ON = "rate_on"
RATE_OFF = "rate_off"
POISSON_POP_SIZE = 'poisson_pop_size'
POISSON_KEY = 'poisson_key'
CROSS_ENTROPY = 'cross_entropy'
ETA = 'eta'
NUMBER_OF_CUES = 'number_of_cues'

DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
# EP_A = "ep_a"
# E_BAR = "e_bar"
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


class NeuronModelLeftRightReadout(AbstractStandardNeuronComponent):
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac",
        # "_mean_isi_ticks",
        # "_time_to_spike_ticks",
        # "_time_since_last_spike",
        # "_rate_at_last_setting",
        # "_rate_update_threshold",
        # "_prob_command",
        "__rate_off",
        "__rate_on",
        "__l",
        "__w_fb",
        "__window_size",
        "__eta",
        "__mean_l",
        "__mean_r",
        "__cross_entropy",
        "__poisson_key",
        "__poisson_pop_size",
        "__n_keys_in_target",
        "__number_of_cues"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            # mean_isi_ticks, time_to_spike_ticks,
            # rate_update_threshold,
            # prob_command,
            rate_on, rate_off, poisson_pop_size, l, w_fb, eta, window_size,
            number_of_cues):

        # global_data_types = [
        #             DataType.UINT32,  # MARS KISS seed
        #             DataType.UINT32,  # MARS KISS seed
        #             DataType.UINT32,  # MARS KISS seed
        #             DataType.UINT32,  # MARS KISS seed
        #             DataType.S1615,    # ticks_per_second
        #             DataType.S1615,    # global mem pot
        #             DataType.S1615,    # global mem pot 2
        #             DataType.S1615,    # rate on
        #             DataType.S1615,    # rate off
        #             DataType.S1615,    # mean left activation
        #             DataType.S1615,    # mean right activation
        #             DataType.S1615,    # cross entropy
        #             DataType.UINT32,   # poisson key
        #             DataType.UINT32,   # poisson pop size
        #             DataType.S1615,    # eta
        #             DataType.UINT32,   # number of cues
        #             ]
        struct_neuron_vals = [
            (DataType.S1615, V),  # v
            (DataType.S1615, V_REST),  # v_rest
            (DataType.S1615, CM), # r_membrane (= tau_m / cm)
            (DataType.S1615, TAU_M), # exp_tc (= e^(-ts / tau_m))
            (DataType.S1615, I_OFFSET), # i_offset
            (DataType.S1615, V_RESET), # v_reset
            (DataType.S1615, TAU_REFRAC), # tau_refrac
            (DataType.INT32, REFRACT_TIMER), # count_refrac
            (DataType.S1615, TIMESTEP), # timestep
            # Learning signal
            (DataType.S1615, L), # L
            (DataType.S1615, W_FB), # w_fb
            (DataType.UINT32, WINDOW_SIZE),    # window_size
            # former global parameters
            (DataType.UINT32, SEED1),
            (DataType.UINT32, SEED2),
            (DataType.UINT32, SEED3),
            (DataType.UINT32, SEED4),  #
            (DataType.S1615, TICKS_PER_SECOND),
            (DataType.S1615, TIME_SINCE_LAST_SPIKE),  # apparently set to 0.0 on first timestep
            (DataType.S1615, RATE_AT_LAST_SETTING),  # apparently set to 0.0 on first timestep
            (DataType.S1615, RATE_ON),
            (DataType.S1615, RATE_OFF),
            (DataType.S1615, MEAN_L),
            (DataType.S1615, MEAN_R),
            (DataType.S1615, CROSS_ENTROPY),
            (DataType.UINT32, POISSON_KEY),
            (DataType.UINT32, POISSON_POP_SIZE),
            (DataType.S1615, ETA),
            (DataType.UINT32, NUMBER_OF_CUES)
        ]


        # Synapse states - always initialise to zero
        for n in range(SYNAPSES_PER_NEURON):
            struct_neuron_vals.extend(
                [(DataType.S1615, DELTA_W+str(n)),
                 (DataType.S1615, Z_BAR_OLD+str(n)),
                 (DataType.S1615, Z_BAR+str(n)),
                 (DataType.UINT32, UPDATE_READY+str(n))])

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
        # self._mean_isi_ticks = mean_isi_ticks
        # self._time_to_spike_ticks = time_to_spike_ticks
        # self._time_since_last_spike = 0 # this should be initialised to zero - we know nothing about before the simulation
        # self._rate_at_last_setting = 0
        # self._rate_update_threshold = 2
        # self._prob_command = prob_command
        self.__rate_off = rate_off
        self.__rate_on = rate_on
        self.__mean_l = 0.0
        self.__mean_r = 0.0
        self.__cross_entropy = 0.0
        self.__poisson_key = 0 # None TODO: work out how to pass this in
        self.__poisson_pop_size = poisson_pop_size
        self.__l = l
        self.__w_fb = w_fb
        self.__eta = eta
        self.__window_size = window_size
        self.__number_of_cues = number_of_cues

        self.__n_keys_in_target = poisson_pop_size * 4

    def set_poisson_key(self, p_key):
        self.__poisson_key = p_key

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

        parameters[L] = self.__l
        parameters[W_FB] = self.__w_fb
        parameters[WINDOW_SIZE] = self.__window_size
        # These should probably have defaults earlier than this
        parameters[SEED1] = 10065
        parameters[SEED2] = 232
        parameters[SEED3] = 3634
        parameters[SEED4] = 4877

        # parameters[PROB_COMMAND] = self._prob_command
        parameters[RATE_ON] = self.__rate_on
        parameters[RATE_OFF] = self.__rate_off

        parameters[TICKS_PER_SECOND] = 0.0 # set in get_valuers()
        parameters[TIME_SINCE_LAST_SPIKE] = 0.0
        parameters[RATE_AT_LAST_SETTING] = 0.0
        parameters[POISSON_POP_SIZE] = self.__poisson_pop_size
        # parameters[RATE_UPDATE_THRESHOLD] = self._rate_update_threshold
#         parameters[TARGET_DATA] = self._target_data
        parameters[MEAN_L] = self.__mean_l
        parameters[MEAN_R] = self.__mean_r
        parameters[CROSS_ENTROPY] = self.__cross_entropy
        parameters[POISSON_KEY] = self.__poisson_key # not sure this is needed here
        print("in add_parameters, poisson key is ", self.__poisson_key)
        parameters[POISSON_POP_SIZE] = self.__poisson_pop_size
        parameters[ETA] = self.__eta
        parameters[NUMBER_OF_CUES] = self.__number_of_cues

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0

        #learning params
        state_variables[L] = self.__l
        # state_variables[MEAN_ISI_TICKS] = self._mean_isi_ticks
        # state_variables[TIME_TO_SPIKE_TICKS] = self._time_to_spike_ticks # could eventually be set from membrane potential
        # state_variables[TIME_SINCE_LAST_SPIKE] = self._time_since_last_spike
        # state_variables[RATE_AT_LAST_SETTING] = self._rate_at_last_setting

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = 0
            state_variables[Z_BAR_OLD+str(n)] = 0
            state_variables[Z_BAR+str(n)] = 0
            # state_variables[EP_A+str(n)] = 0
            # state_variables[E_BAR+str(n)] = 0
            state_variables[UPDATE_READY+str(n)] = self.__window_size


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
    #             parameters[W_FB],
    #             parameters[WINDOW_SIZE]
    #             ]
    #
    #     # create synaptic state - init all state to zero
    #     eprop_syn_init = [0,    # delta w
    #                       0,    # z_bar_inp
    #                       0,#,    # z_bar
    #                       # 0,    # el_a
    #                       # 0]    # e_bar
    #                       self._window_size, #int(numpy.random.rand()*1024)      # update_ready
    #                       ]
    #     # extend to appropriate fan-in
    #     values.extend(eprop_syn_init * SYNAPSES_PER_NEURON)
    #
    #     return values
    #
    # @overrides(AbstractNeuronModel.update_values)
    # def update_values(self, values, parameters, state_variables):
    #
    #     # Read the data
    #     (_v, _v_rest, _r_membrane, _exp_tc, _i_offset, _count_refrac,
    #     _v_reset, _tau_refrac,
    #     _l, _w_fb, window_size, delta_w, z_bar_old, z_bar, update_ready) = values  # Not sure this will work with the new array of synapse!!!
    #     # todo check alignment on this
    #
    #     # Copy the changed data only
    #     state_variables[V] = _v
    #
    #     state_variables[L] = _l
    #
    #     for n in range(SYNAPSES_PER_NEURON):
    #         state_variables[DELTA_W+str(n)] = delta_w[n]
    #         state_variables[Z_BAR_OLD+str(n)] = z_bar_old[n]
    #         state_variables[Z_BAR+str(n)] = z_bar[n]
    #         # state_variables[EP_A+str(n)] = ep_a[n]
    #         # state_variables[E_BAR+str(n)] = e_bar[n]
    #         state_variables[UPDATE_READY] = update_ready[n]
    #
    # # Global params
    # @inject_items({"machine_time_step": "MachineTimeStep"})
    # @overrides(AbstractNeuronModel.get_global_values,
    #            additional_arguments={'machine_time_step'})
    # def get_global_values(self, machine_time_step):
    #     vals = [
    #             1, # seed 1
    #             2, # seed 2
    #             3, # seed 3
    #             4, # seed 4
    #             MICROSECONDS_PER_SECOND / float(machine_time_step), # ticks_per_second
    #             0.0, # set to 0, as will be set in first timestep of model anyway
    #             0.0, # set to 0, as will be set in first timestep of model anyway
    #             self._rate_on,
    #             self._rate_off,
    #             self._mean_l,
    #             self._mean_r,
    #             self._cross_entropy,
    #             self._poisson_key,
    #             self._poisson_pop_size,
    #             self._eta,
    #             self._number_of_cues
    #             ]
    #
    #     return vals

    # @property
    # def prob_command(self):
    #     return self.__prob_command

    # @prob_command.setter
    # def prob_command(self, prob_command):
    #     self._prob_command = prob_command

    @property
    def rate_on(self):
        return self.__rate_on

    @rate_on.setter
    def rate_on(self, rate_on):
        self.__rate_on = rate_on

    @property
    def rate_off(self):
        return self.__rate_off

    @rate_on.setter
    def rate_on(self, rate_off):
        self.__rate_off = rate_off

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
    def w_fb(self, new_value):
        self.__w_fb = new_value

    @property
    def window_size(self):
        return self.__window_size

    @window_size.setter
    def window_size(self, new_value):
        self.__window_size = new_value

    # @property
    # def mean_isi_ticks(self):
    #     return self._mean_isi_ticks
    #
    # @mean_isi_ticks.setter
    # def mean_isi_ticks(self, new_mean_isi_ticks):
    #     self._mean_isi_ticks = new_mean_isi_ticks
    #
    # @property
    # def time_to_spike_ticks(self):
    #     return self._time_to_spike_ticks
    #
    # @mean_isi_ticks.setter
    # def time_to_spike_ticks(self, new_time_to_spike_ticks):
    #     self._time_to_spike_ticks = new_time_to_spike_ticks
