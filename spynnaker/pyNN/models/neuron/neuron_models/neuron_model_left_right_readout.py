import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel

# constants
SYNAPSES_PER_NEURON = 250   # around 415 with only 3 in syn_state
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
RATE_ON = "rate_on"
RATE_OFF = "rate_off"
POISSON_POP_SIZE = 'poisson_pop_size'

DELTA_W = "delta_w"
Z_BAR_OLD = "z_bar_old"
Z_BAR = "z_bar"
# EP_A = "ep_a"
# E_BAR = "e_bar"
UPDATE_READY = "update_ready"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms'
}


class NeuronModelLeftRightReadout(AbstractNeuronModel):
    __slots__ = [
        "_v_init",
        "_v_rest",
        "_tau_m",
        "_cm",
        "_i_offset",
        "_v_reset",
        "_tau_refrac",
        # "_mean_isi_ticks",
        # "_time_to_spike_ticks",
        # "_time_since_last_spike",
        # "_rate_at_last_setting",
        # "_rate_update_threshold",
        # "_prob_command",
        "_rate_off",
        "_rate_on",
        "_l",
        "_w_fb",
        "_window_size",
        "_eta",
        "_mean_l",
        "_mean_r",
        "_cross_entropy",
        "_poisson_key",
        "_poisson_pop_size",
        "_n_keys_in_target"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            # mean_isi_ticks, time_to_spike_ticks,
            # rate_update_threshold,
            # prob_command,
            rate_on, rate_off, poisson_pop_size, l, w_fb, eta, window_size):

        global_data_types = [
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.UINT32,  # MARS KISS seed
                    DataType.S1615,    # ticks_per_second
                    DataType.S1615,    # global mem pot
                    DataType.S1615,    # global mem pot 2
                    DataType.S1615,    # rate on
                    DataType.S1615,    # rate off
                    DataType.S1615,    # mean left activation
                    DataType.S1615,    # mean right activation
                    DataType.S1615,    # cross entropy
                    DataType.UINT32,   # poisson key
                    DataType.UINT32,   # poisson pop size
                    DataType.S1615,    # eta
                    ]
        data_types = [
            DataType.S1615,  # v
            DataType.S1615,  # v_rest
            DataType.S1615,  # r_membrane (= tau_m / cm)
            DataType.S1615,  # exp_tc (= e^(-ts / tau_m))
            DataType.S1615,  # i_offset
            DataType.INT32,  # count_refrac
            DataType.S1615,  # v_reset
            DataType.INT32,  # tau_refrac
            # Learning signal
            DataType.S1615,  # L
            DataType.S1615,  # w_fb
            DataType.UINT32    # window_size
        ]

        # Synapse states - always initialise to zero
        eprop_syn_state = [ # synaptic state, one per synapse (kept in DTCM)
                DataType.S1615, # delta_w
                DataType.S1615, # z_bar_old
                DataType.S1615, # z_bar
                # DataType.S1615, # ep_a
                # DataType.S1615, # e_bar
                DataType.INT32   # update_ready
            ]
        # Extend to include fan-in for each neuron
        data_types.extend(eprop_syn_state * SYNAPSES_PER_NEURON)

        super(NeuronModelLeftRightReadout, self).__init__(
            data_types=data_types,

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
        # self._mean_isi_ticks = mean_isi_ticks
        # self._time_to_spike_ticks = time_to_spike_ticks
        # self._time_since_last_spike = 0 # this should be initialised to zero - we know nothing about before the simulation
        # self._rate_at_last_setting = 0
        # self._rate_update_threshold = 2
        # self._prob_command = prob_command
        self._rate_off = rate_off
        self._rate_on = rate_on
        self._mean_l = 0.0
        self._mean_r = 0.0
        self._cross_entropy = 0.0
        self._poisson_key = None
        self._poisson_pop_size = poisson_pop_size
        self._l = l
        self._w_fb = w_fb
        self._eta = eta
        self._window_size = window_size

        self._n_keys_in_target = poisson_pop_size * 4

    def set_poisson_key(self, p_key):
        self._poisson_key = p_key

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
        parameters[L] = self._l
        parameters[W_FB] = self._w_fb
        parameters[WINDOW_SIZE] = self._window_size
        parameters[SEED1] = 10065
        parameters[SEED2] = 232
        parameters[SEED3] = 3634
        parameters[SEED4] = 4877

        # parameters[PROB_COMMAND] = self._prob_command
        parameters[RATE_ON] = self._rate_on
        parameters[RATE_OFF] = self._rate_off

        parameters[TICKS_PER_SECOND] = 0 # set in get_valuers()
        parameters[POISSON_POP_SIZE] = self._poisson_pop_size
        # parameters[RATE_UPDATE_THRESHOLD] = self._rate_update_threshold
#         parameters[TARGET_DATA] = self._target_data

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self._v_init
        state_variables[COUNT_REFRAC] = 0

        #learning params
        state_variables[L] = self._l
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
            state_variables[UPDATE_READY+str(n)] = self._window_size


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
        values = [state_variables[V],
                parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),

                state_variables[L],
                parameters[W_FB],
                parameters[WINDOW_SIZE]
                ]

        # create synaptic state - init all state to zero
        eprop_syn_init = [0,    # delta w
                          0,    # z_bar_inp
                          0,#,    # z_bar
                          # 0,    # el_a
                          # 0]    # e_bar
                          self._window_size, #int(numpy.random.rand()*1024)      # update_ready
                          ]
        # extend to appropriate fan-in
        values.extend(eprop_syn_init * SYNAPSES_PER_NEURON)

        return values

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_v, _v_rest, _r_membrane, _exp_tc, _i_offset, _count_refrac,
        _v_reset, _tau_refrac,
        _l, _w_fb, window_size, delta_w, z_bar_old, z_bar, update_ready) = values  # Not sure this will work with the new array of synapse!!!
        # todo check alignment on this

        # Copy the changed data only
        state_variables[V] = _v

        state_variables[L] = _l

        for n in range(SYNAPSES_PER_NEURON):
            state_variables[DELTA_W+str(n)] = delta_w[n]
            state_variables[Z_BAR_OLD+str(n)] = z_bar_old[n]
            state_variables[Z_BAR+str(n)] = z_bar[n]
            # state_variables[EP_A+str(n)] = ep_a[n]
            # state_variables[E_BAR+str(n)] = e_bar[n]
            state_variables[UPDATE_READY] = update_ready[n]

    # Global params
    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'machine_time_step'})
    def get_global_values(self, machine_time_step):
        vals = [
                1, # seed 1
                2, # seed 2
                3, # seed 3
                4, # seed 4
                MICROSECONDS_PER_SECOND / float(machine_time_step), # ticks_per_second
                0.0, # set to 0, as will be set in first timestep of model anyway
                0.0, # set to 0, as will be set in first timestep of model anyway
                self._rate_on,
                self._rate_off,
                self._mean_l,
                self._mean_r,
                self._cross_entropy,
                self._poisson_key,
                self._poisson_pop_size,
                self._eta
                ]
        
        return vals

    @property
    def prob_command(self):
        return self._prob_command

    # @prob_command.setter
    # def prob_command(self, prob_command):
    #     self._prob_command = prob_command

    @property
    def rate_on(self):
        return self._rate_on

    @rate_on.setter
    def rate_on(self, rate_on):
        self._rate_on = rate_on

    @property
    def rate_off(self):
        return self._rate_off

    @rate_on.setter
    def rate_on(self, rate_off):
        self._rate_off = rate_off

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

    @property
    def w_fb(self):
        return self._w_fb

    @w_fb.setter
    def w_fb(self, new_value):
        self._w_fb = new_value

    @property
    def window_size(self):
        return self._window_size

    @window_size.setter
    def window_size(self, new_value):
        self._window_size = new_value

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