"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p

from spynnaker.pyNN.models.neuron.builds.if_curr_exp \
    import IFCurrExp as IF_curr_exp
from spynnaker.pyNN.models.spike_source.spike_source_array import \
    SpikeSourceArray

CELL_PARAMS_LIF = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                   'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                   'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}


class TestRun(object):

    def __init__(self):
        self._recorded_v = []
        self._recorded_spikes = []
        self._recorded_gsyn = []
        self._input_spikes_recorded = []
        self._weights = []
        self._delays = []

    def do_run(
            self, n_neurons, time_step=1, max_delay=144.0,
            input_class=SpikeSourceArray, spike_times=None, rate=None,
            start_time=None, duration=None, spike_times_list=None,
            placement_constraint=None, weight_to_spike=2.0, delay=17,
            neurons_per_core=10, cell_class=IF_curr_exp, constraint=None,
            cell_params=CELL_PARAMS_LIF, run_times=None, reset=False,
            extract_between_runs=True, new_pop=False,
            record_input_spikes=False, record=True, get_spikes=None,
            spike_path=None, record_v=True, get_v=None, v_path=None,
            record_gsyn=True, get_gsyn=None, gsyn_path=None,
            use_loop_connections=True, get_weights=False, get_delays=False,
            end_before_print=False, randomise_v_init=False):
        """

        :param n_neurons: Number of Neurons in chain
        :type  n_neurons: int
        :param time_step: time step value to be used in p.setup
        :type time_step: float
        :param max_delay: max_delay value to be used in p.setup
        :type max_delay: float
        :param rate: the rate of the SSP to fire at
        :type rate: float
        :param start_time: the start time for the SSP
        :type start_time: float
        :param duration: the length of time for the SSP to fire for
        :type duration: float
        :param input_class: the class for inputs spikes (SSA or SSP)
        :type input_class: SpikeSourceArray, SpikeSourcePoisson
        :param spike_times: times the SSA sends in spikes
        :type spike_times: matrix of int times the SSA sends in spikes
        :param spike_times_list: list of times the SSA sends in spikes
            - must be the same length as  run times
            - If set the spike_time parameter is ignored
        :type spike_times_list: list of matrix of
            int times the SSA sends in spikes
        :param placement_constraint: x, y and p values to add a
            placement_constraint to population[0]
        :type (int, int, int)
        :type weight_to_spike: float
        :param delay: time delay in the single connectors in the spike chain
        :type delay: float
        :param neurons_per_core: Number of neurons per core.
            If set to None no  set_number_of_neurons_per_core call will be made
        :type neurons_per_core: int or None
        :param constraint: A Constraint to be place on populations[0]
        :type constraint: AbstractConstraint
        :param cell_class: class to be used for the main population
            Not used by any test at the moment
        :type cell_class: AbstractPopulationVertex
        :param cell_params: values for the main population
            Not used by any test at the moment
            Note: the values must match what is expected by the cellclass
        :type cell_params: dict
        :param run_times: times for each run.
            A zero will skip run but trigger reset and get date ext as set
        :type run_times: list of int
        :param reset: if True will call reset after each run except the last
        :type reset: bool
        :param extract_between_runs: If True reads V, gysn and spikes
            between each run.
        :type extract_between_runs: bool
        :param new_pop: If True will add a new population before the second run
        :type new_pop: bool
        :param record_input_spikes: check for recording input spikes
        :type record_input_spikes: bool
        :param record: If True will aks for spikes to be recorded
        :type record: bool
        :param get_spikes: If set overrides the normal behaviour
            of getting spikes if and only if record is True.
            If left None the value of record is used.
        :type get_spikes: bool
        :param spike_path: The path to print(write) the last spike data too
        :type spike_path: str or None
        :param record_v: If True will aks for voltage to be recorded
        :type record_v: bool
        :param get_v: If set overrides the normal behaviour
            of getting v if and only if record_v is True.
            If left None the value of record_v is used.
        :type get_v: bool
        :param v_path: The path to print(write) the last v data too
        :type v_path: str or None
        :param record_gsyn: If True will aks for gsyn to be recorded
        :type record_gsyn: bool
        :param get_gsyn: If set overrides the normal behaviour
            of getting gsyn if and only if record_gsyn is True.
            If left None the value of record_gsyn is used.
        :type get_v: bool
        :param gsyn_path: The path to print(write) the last gsyn data too
        :type gsyn_path: str or None
        :param get_weights: If True weights will be gotten
        :type get_weights: bool
        :param get_delays: If True delays will be gotten
        :type get_delays: bool
        :param end_before_print: If True will call end() before running the \
            optional print commands.
            Note: end will always be called twice even if no print path
            provided
            WARNING: This is expected to cause an Exception \
                if spike_path, v_path or gsyn_path provided
        :type end_before_print: bool
        :param randomise_v_init: randomises the v_init of the output pop.
        :type randomise_v_init: bool
        :param use_loop_connections: True will put looping connections in.
            falswont
        :type use_loop_connections: bool
        """

        if run_times is None:
            run_times = [1000]

        if spike_times is None:
            spike_times = [[0]]

        if get_spikes is None:
            get_spikes = record

        if get_v is None:
            get_v = record_v

        if get_gsyn is None:
            get_gsyn = record_gsyn

        p.setup(timestep=time_step, min_delay=1.0, max_delay=max_delay)
        if neurons_per_core is not None:
            p.set_number_of_neurons_per_core("IF_curr_exp", neurons_per_core)

        populations = list()
        projections = list()

        loop_connections = list()
        for i in range(0, n_neurons):
            single_connection = \
                (i, ((i + 1) % n_neurons), weight_to_spike, delay)
            loop_connections.append(single_connection)

        injection_connection = [(0, 0, weight_to_spike, 1)]

        run_count = 0
        if spike_times_list is None:
            spike_array = {'spike_times': spike_times}
        else:
            spike_array = {'spike_times': spike_times_list[run_count]}

        populations.append(p.Population(
            n_neurons, cell_class, cell_params, label='pop_1'))

        if placement_constraint is not None:
            (x, y, proc) = placement_constraint
            populations[0].add_placement_constraint(x=x, y=y, p=proc)

        if randomise_v_init:
            rng = p.NumpyRNG(seed=28375)
            v_init = p.RandomDistribution('uniform', [-60, -40], rng)
            populations[0].randomInit(v_init)

        if constraint is not None:
            populations[0].set_constraint(constraint)

        if input_class == SpikeSourceArray:
            populations.append(p.Population(
                1, input_class, spike_array, label='inputSSA_1'))
        else:
            populations.append(p.Population(
                1, input_class,
                {'rate': rate, 'start': start_time, 'duration': duration},
                label='inputSSP_1'))

        # handle projections
        if use_loop_connections:
            projections.append(p.Projection(populations[0], populations[0],
                               p.FromListConnector(loop_connections)))

        projections.append(p.Projection(populations[1], populations[0],
                           p.FromListConnector(injection_connection)))

        # handle recording
        if record or spike_path is not None:
            populations[0].record()
        if record_v or v_path is not None:
            populations[0].record_v()
        if record_gsyn or gsyn_path is not None:
            populations[0].record_gsyn()
        if record_input_spikes:
            populations[1].record()

        results = ()

        for runtime in run_times[:-1]:
            # This looks strange but is to allow getting data before run
            if runtime > 0:
                p.run(runtime)
            run_count += 1

            if extract_between_runs:
                self._get_data(
                    populations[0], populations[1], get_spikes, get_v,
                    get_gsyn, record_input_spikes)
                if get_weights:
                    self._weights.append(projections[0].getWeights())
                if get_delays:
                    self._delays.append(projections[0].getDelays())

            if new_pop:
                populations.append(
                    p.Population(n_neurons, cell_class, cell_params,
                                 label='pop_2'))
                injection_connection = [(n_neurons - 1, 0, weight_to_spike, 1)]
                new_projection = p.Projection(
                    populations[0], populations[2],
                    p.FromListConnector(injection_connection))
                projections.append(new_projection)

            if spike_times_list is not None:
                populations[1].tset("spike_times", spike_times_list[run_count])

            if reset:
                p.reset()

        p.run(run_times[-1])

        self._get_data(
            populations[0], populations[1], get_spikes, get_v, get_gsyn,
            record_input_spikes)
        if get_weights:
            self._weights.append(projections[0].getWeights())
        if get_delays:
            self._delays.append(projections[0].getDelays())

        if end_before_print:
            if v_path is not None or spike_path is not None or \
                    gsyn_path is not None:
                print "NOTICE! end is being called before print.. commands " \
                      "which could cause an exception"
            p.end()

        if v_path is not None:
            populations[0].print_v(v_path)
        if spike_path is not None:
            populations[0].printSpikes(spike_path)
        if gsyn_path is not None:
            populations[0].print_gsyn(gsyn_path)
        p.end()

        return results

    def get_output_pop_gsyn(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._recorded_gsyn) == 0:
            return None
        if len(self._recorded_gsyn) == 1:
            return self._recorded_gsyn[0]
        return self._recorded_gsyn

    def get_output_pop_voltage(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._recorded_v) == 0:
            return None
        if len(self._recorded_v) == 1:
            return self._recorded_v[0]
        return self._recorded_v

    def get_output_pop_spikes(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._recorded_spikes) == 0:
            return None
        if len(self._recorded_spikes) == 1:
            return self._recorded_spikes[0]
        return self._recorded_spikes

    def get_spike_source_spikes(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._input_spikes_recorded) == 0:
            return None
        if len(self._input_spikes_recorded) == 1:
            return self._input_spikes_recorded[0]
        return self._input_spikes_recorded

    def get_weights(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._weights) == 0:
            return None
        if len(self._weights) == 1:
            return self._weights[0]
        return self._weights

    def get_delay(self):
        """

        ;return if not recorded returns None
            if recorded once returns a numpy array
            if recorded more than once returns a list of numpy arrays
        :rtype: None, nparray or list of nparray
        """
        if len(self._delays) == 0:
            return None
        if len(self._delays) == 1:
            return self._delays[0]
        return self._delays

    def _get_data(
            self, output_population, input_population, get_spikes, get_v,
            get_gsyn, input_pop_record_spikes):

        if get_v:
            self._recorded_v.append(output_population.get_v(
                compatible_output=True))

        if get_gsyn:
            self._recorded_gsyn.append(output_population.get_gsyn(
                compatible_output=True))

        if get_spikes:
            self._recorded_spikes.append(output_population.getSpikes(
                compatible_output=True))

        if input_pop_record_spikes:
            self._input_spikes_recorded.append(input_population.getSpikes(
                compatible_output=True))
