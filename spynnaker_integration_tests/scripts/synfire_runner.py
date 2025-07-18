# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Synfirechain-like example
"""
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

import neo
from numpy import floating
from numpy.typing import NDArray
import pyNN.spiNNaker as p
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.models.projection import Projection
from spynnaker.pyNN.utilities import neo_convertor

CELL_PARAMS_LIF = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                   'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                   'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}


class SynfireRunner(object):
    # pylint: disable=attribute-defined-outside-init

    def __init__(self) -> None:
        self.__init_object_state()

    def do_run(
            self, n_neurons: int, time_step: float = 1,
            input_class: Type = p.SpikeSourceArray,
            spike_times: Optional[List[List[int]]] = None,
            rate: Optional[float] = None, start_time: Optional[int] = None,
            duration: Optional[float] = None, seed: Optional[int] = None,
            spike_times_list: None = None,
            placement_constraint: Optional[Tuple[int, int]] = None,
            weight_to_spike: float = 2.0, delay: float = 17,
            neurons_per_core: Optional[int] = 10,
            cell_class: Type = p.IF_curr_exp,
            constraint: None = None,
            cell_params: Dict[str, float] = CELL_PARAMS_LIF,
            run_times: Optional[List[int]] = None,
            reset: Literal[False] = False, extract_between_runs: bool = True,
            set_between_runs: Optional[List[Tuple[int, str, float]]] = None,
            new_pop: Literal[False] = False,
            record_input_spikes: bool = False,
            record_input_spikes_7: Literal[False] = False,
            record: bool = True, get_spikes: Optional[bool] = None,
            spike_path: None = None, record_7: bool = False,
            record_v: bool = True, get_v: Optional[bool] = None,
            v_path: None = None, record_v_7: bool = False,
            v_sampling_rate: Optional[int] = None,
            record_gsyn_exc: bool = True, record_gsyn_inh: bool = True,
            get_gsyn_exc: Optional[bool] = None,
            get_gsyn_inh: Optional[bool] = None,
            gsyn_path_exc: None = None, gsyn_path_inh: None = None,
            record_gsyn_exc_7: bool = False,
            record_gsyn_inh_7: Literal[False] = False,
            gsyn_exc_sampling_rate: Optional[int] = None,
            gsyn_inh_sampling_rate: None = None,
            get_all: Literal[False] = False,
            use_spike_connections: Literal[True] = True,
            use_wrap_around_connections: bool = True,
            get_weights: bool = False, get_delays: bool = False,
            end_before_print: Literal[False] = False,
            randomise_v_init: Literal[False] = False) -> Tuple:
        """

        :param n_neurons: Number of Neurons in chain
        :param time_step: time step value to be used in p.setup
        :param rate: the rate of the SSP to fire at
        :param start_time: the start time for the SSP
        :param duration: the length of time for the SSP to fire for
        :param seed: Random seed
        :param input_class: the class for inputs spikes (SSA or SSP)
        :param spike_times: times the SSA sends in spikes
        :param spike_times_list: list of times the SSA sends in spikes
            - must be the same length as  run times
            - If set the spike_time parameter is ignored
        :param weight_to_spike: weight for the OneToOne Connector.\
            Not used by any test at the moment
        :param delay: time delay in the single connectors in the spike chain
        :param neurons_per_core: Number of neurons per core.\
            If set to None, no set_number_of_neurons_per_core call will be made
        :param constraint: A Constraint to be place on populations[0]
        :param cell_class: class to be used for the main population.\
            Not used by any test at the moment
        :param cell_params: values for the main population.\
            Not used by any test at the moment.\
            Note: the values must match what is expected by the cellclass
        :param run_times: times for each run.\
            A zero will skip run but trigger reset and get date ext as set
        :param reset: if True will call reset after each run except the last
        :param extract_between_runs: \
            If True reads V, gysn and spikes between each run.
        :param set_between_runs: set instructions to be carried out between\
            runs. Should be a list of tuples.
            First element of each tuple is 0 or 1:
              * 0 for main population
              * 1 for input population
            Second element a String for name of property to change.
            Third element the new value
        :param new_pop: If True will add a new population before the second run
        :param record_input_spikes: check for recording input spikes
        :param record_input_spikes_7: \
            Check for recording input spikes in PyNN7 format
        :param record: If True will asks for spikes to be recorded
        :param get_spikes: If set overrides the normal behaviour\
            of getting spikes if and only if record is True.\
            If left None the value of record is used.
        :param spike_path: The path to print(write) the last spike data too
        :param record_7: \
            If True will asks for spikes to be recorded in PyNN7 format
        :param record_v: If True will ask for voltage to be recorded
        :param get_v: If set overrides the normal behaviour\
            of getting v if and only if record_v is True.\
            If left None the value of record_v is used.
        :param v_path: The path to print(write) the last v data too
        :param get_v_7: If True ???????
        :param record_v_7: If True will ask for voltage to be recorded\
            in PyNN7 format
        :param v_sampling_rate: Rate at which to sample v.
        :param record_gsyn_exc: If True will aks for gsyn exc to be recorded
        :param record_gsyn_exc: If True will ask for gsyn exc to be recorded
        :param record_gsyn_inh: If True will ask for gsyn inh to be recorded
        :param gsyn_path_exc: \
            The path to print(write) the last gsyn exc data to.
        :param get_gsyn_exc: If set overrides the normal behaviour\
            of getting gsyn exc if and only if record_gsyn_exc is True.\
            If left None the value of record_gsyn_exc is used.
        :param get_gsyn_inh: If set overrides the normal behaviour\
            of getting gsyn inh if and only if record_gsyn_inh is True.\
            If left None the value of record_gsyn_ihn is used.
        :param gsyn_path_inh: \
            The path to print(write) the last gsyn in the data to.
        :param record_gsyn_exc_7: \
            If True will ask for gsyn exc to be recorded in PyNN 7 format
        :param record_gsyn_inh_7: \
            If True will ask for gsyn inh to be recorded in PyNN 7 format
        :param get_all: if True will obtain another neo object with all the
            data set to be recorded by any other parameter
        :param get_weights: If True set will add a weight value to the return
        :param get_delays: If True delays will be gotten
        :param end_before_print: If True will call end() before running the\
            optional print commands.
            Note: end will always be called twice even if no print path\
            provided
            WARNING: This is expected to cause an Exception \
                if spike_path, v_path or gsyn_path provided
        :param randomise_v_init: randomises the v_init of the output pop.
        :param use_loop_connections: \
            True will put looping connections in. False won't.
        :return (v, gsyn, spikes, weights .....)
            v: Voltage after last or each run (if requested else None)
            gysn: gysn after last or each run (if requested else None)
            spikes: spikes after last or each run (if requested else None)
            weights: weights after last or each run (if requested else skipped)

            All three/four values will repeated once per run is requested
        """
        self.__init_object_state()

        # Initialise/verify various values
        cell_params, run_times, _set_between_runs, spike_times, get_spikes, \
            get_v, get_gsyn_exc, get_gsyn_inh = self.__verify_parameters(
                cell_params, run_times, set_between_runs, spike_times,
                get_spikes, record, record_7, spike_path, get_v, record_v,
                record_v_7, v_path, get_gsyn_exc, record_gsyn_exc,
                record_gsyn_exc_7, gsyn_path_exc, get_gsyn_inh,
                record_gsyn_inh, record_gsyn_inh_7, gsyn_path_inh)

        p.setup(timestep=time_step)
        if neurons_per_core is not None:
            p.set_number_of_neurons_per_core(p.IF_curr_exp, neurons_per_core)

        populations, projections, run_count = self.__create_synfire_chain(
            n_neurons, cell_class, cell_params, use_wrap_around_connections,
            weight_to_spike, delay, spike_times, spike_times_list,
            placement_constraint, randomise_v_init, seed, constraint,
            input_class, rate, start_time, duration, use_spike_connections)

        # handle recording
        if record or record_7 or spike_path:
            populations[0].record("spikes")
        if record_v or record_v_7 or v_path:
            populations[0].record(
                variables="v", sampling_interval=v_sampling_rate)
        if record_gsyn_exc or record_gsyn_exc_7 or gsyn_path_exc:
            populations[0].record(
                variables="gsyn_exc", sampling_interval=gsyn_exc_sampling_rate)
        if record_gsyn_inh or record_gsyn_inh_7 or gsyn_path_inh:
            populations[0].record(
                variables="gsyn_inh", sampling_interval=gsyn_inh_sampling_rate)
        if record_input_spikes or record_input_spikes_7:
            populations[1].record("spikes")

        results = self.__run_sim(
            run_times, populations, projections, run_count, spike_times_list,
            extract_between_runs, get_spikes, record_7, get_v, record_v_7,
            get_gsyn_exc, record_gsyn_exc_7, get_gsyn_inh, record_gsyn_inh_7,
            record_input_spikes, record_input_spikes_7, get_all, get_weights,
            get_delays, new_pop, n_neurons, cell_class, cell_params,
            weight_to_spike, _set_between_runs, reset)

        self._get_data(populations[0], populations[1], get_spikes, record_7,
                       get_v, record_v_7, get_gsyn_exc, record_gsyn_exc_7,
                       get_gsyn_inh, record_gsyn_inh_7, record_input_spikes,
                       record_input_spikes_7, get_all)

        self._get_weight_delay(projections[0], get_weights, get_delays)

        if end_before_print:
            if v_path is not None or spike_path is not None or \
                    gsyn_path_exc is not None or gsyn_path_inh is not None:
                print("NOTICE! end is being called before print.. commands "
                      "which could cause an exception")
            p.end()

        if v_path is not None:
            populations[0].write_data(v_path, "v")
        if spike_path is not None:
            populations[0].write_data(spike_path, "spikes")
        if gsyn_path_exc is not None:
            populations[0].write_data(gsyn_path_exc, "gsyn_exc")
        if gsyn_path_inh is not None:
            populations[0].write_data(gsyn_path_inh, "gsyn_inh")
        if not end_before_print:
            p.end()

        return results

    def __init_object_state(self) -> None:
        """ Initialises the object's internal state. """
        self._recorded_v_list: List[neo.Block] = []
        self._recorded_v_7: Optional[NDArray[floating]] = None
        self._recorded_spikes_list: List[neo.Block] = []
        self._recorded_spikes_7: Optional[NDArray[floating]] = None
        self._recorded_gsyn_exc_list: List[neo.Block] = []
        self._recorded_gsyn_exc_7: Optional[NDArray[floating]] = None
        self._recorded_gsyn_inh_list: List[neo.Block] = []
        self._recorded_gsyn_inh_7: Optional[NDArray[floating]] = None
        self._recorded_all_list: List[neo.Block] = []
        self._input_spikes_recorded_list: List[neo.Block] = []
        self._input_spikes_recorded_7: Any = []
        self._weights: List[ConnectionHolder] = []
        self._delays: List[ConnectionHolder] = []

    @staticmethod
    def __verify_parameters(
            cell_params: Dict[str, float], run_times: Optional[List[int]],
            set_between_runs: Optional[List[Tuple[int, str, float]]],
            spike_times: Optional[List[List[int]]],
            get_spikes: Optional[bool], record: bool, record_7: bool,
            spike_path: None, get_v: Optional[bool], record_v: bool,
            record_v_7: bool, v_path: None, get_gsyn_exc: Optional[bool],
            record_gsyn_exc: bool, record_gsyn_exc_7: bool,
            gsyn_path_exc: None, get_gsyn_inh: Optional[bool],
            record_gsyn_inh: bool, record_gsyn_inh_7: Literal[False],
            gsyn_path_inh: None
            ) -> Tuple[Dict[str, float], List[int],
                       List[Tuple[int, str, float]],
                       List[List[int]], bool, bool, bool, bool]:
        """ Checks that parameters to do_run are reasonable, and sets them up\
            or raises an exception if they aren't. """
        if cell_params is None:
            cell_params = CELL_PARAMS_LIF

        if run_times is None:
            run_times = [1000]

        if set_between_runs is None:
            set_between_runs = []

        if len(set_between_runs) > 0 and len(run_times) != 2:
            raise ValueError("set_between_runs requires exactly 2 run times")

        if spike_times is None:
            spike_times = [[0]]

        if get_spikes is None:
            get_spikes = record
        elif not record:
            if record_7:
                raise NotImplementedError(
                    "record_7 will cause spike recording to be turned on")
            if spike_path:
                raise NotImplementedError(
                    "spike_path will cause spike recording to be turned on")

        if get_v is None:
            get_v = record_v
        elif not record_v:
            if record_v_7:
                raise NotImplementedError(
                    "record_v_7 will cause v recording to be turned on")
            if v_path:
                raise NotImplementedError(
                    "v_path will cause v recording to be turned on")

        if get_gsyn_exc is None:
            get_gsyn_exc = record_gsyn_exc
        elif not record_gsyn_exc:
            if record_gsyn_exc_7:
                raise NotImplementedError(
                    "record_gsyn_exc_7 will cause gsyn_exc recording "
                    "to be turned on")
            if gsyn_path_exc:
                raise NotImplementedError(
                    "gsyn_path_exc will cause gsyn_exc recording "
                    "to be turned on")

        if get_gsyn_inh is None:
            get_gsyn_inh = record_gsyn_inh
        elif not record_gsyn_inh:
            if record_gsyn_inh_7:
                raise NotImplementedError(
                    "record_gsyn_inh_7 will cause gsyn_inh recording "
                    "to be turned on")
            if gsyn_path_inh:
                raise NotImplementedError(
                    "gsyn_path_inh will cause gsyn_exc recording "
                    "to be turned on")

        return (cell_params, run_times, set_between_runs, spike_times,
                get_spikes, get_v, get_gsyn_exc, get_gsyn_inh)

    @staticmethod
    def __create_synfire_chain(
            n_neurons: int, cell_class: Type, cell_params: Dict[str, float],
            use_wrap_around_connections: bool, weight_to_spike: float,
            delay: float, spike_times: Optional[List[List[int]]],
            spike_times_list: None,
            placement_constraint: Optional[Tuple[int, int]],
            randomise_v_init: Literal[False], seed: Optional[int],
            constraint: None, input_class: Type, rate: Optional[float],
            start_time: Optional[int], duration: Optional[float],
            use_spike_connections: Literal[True]
            ) -> Tuple[List[Population], List[Projection], int]:
        """ This actually builds the synfire chain. """
        populations: List[Population] = list()
        projections: List[Projection] = list()

        loop_connections = list()
        if use_wrap_around_connections:
            for i in range(0, n_neurons):
                single_connection = \
                    (i, ((i + 1) % n_neurons), weight_to_spike, delay)
                loop_connections.append(single_connection)
        else:
            for i in range(0, n_neurons - 1):
                single_connection = (i, i + 1, weight_to_spike, delay)
                loop_connections.append(single_connection)

        injection_connection = [(0, 0, weight_to_spike, 1)]

        run_count = 0
        if spike_times_list is None:
            spike_array = {'spike_times': spike_times}
        else:
            spike_array = {'spike_times': spike_times_list[run_count]}

        populations.append(p.Population(
            n_neurons, cell_class(**cell_params), label='pop_1', seed=seed))

        if placement_constraint is not None:
            if len(placement_constraint) == 2:
                (x, y) = placement_constraint
                populations[0].add_placement_constraint(x=x, y=y)
            else:
                (x, y, proc) = placement_constraint
                populations[0].add_placement_constraint(x=x, y=y, p=proc)

        if randomise_v_init:
            v_init = p.RandomDistribution('uniform', [-60, -40])
            populations[0].initialize(v=v_init)

        if constraint is not None:
            populations[0].set_constraint(constraint)

        if input_class == p.SpikeSourceArray:
            populations.append(p.Population(
                1, input_class(**spike_array), label='inputSSA_1'))
        elif seed is None:
            populations.append(p.Population(
                1, input_class(rate=rate, start=start_time, duration=duration),
                label='inputSSP_1'))
        else:
            populations.append(p.Population(
                1, input_class(
                    rate=rate, start=start_time, duration=duration),
                label='inputSSP_1', seed=seed))

        # handle projections
        if use_spike_connections:
            projections.append(
                p.Projection(
                    populations[0], populations[0],
                    p.FromListConnector(loop_connections),
                    p.StaticSynapse(weight=weight_to_spike, delay=delay)))

        projections.append(p.Projection(
            populations[1], populations[0],
            p.FromListConnector(injection_connection),
            p.StaticSynapse(weight=weight_to_spike, delay=1)))

        return populations, projections, run_count

    def __run_sim(
            self, run_times: List[int], populations: List[Population],
            projections: List[Projection], run_count: int,
            spike_times_list: None, extract_between_runs: bool,
            get_spikes: bool, record_7: bool, get_v: bool, record_v_7: bool,
            get_gsyn_exc: bool, record_gsyn_exc_7: bool, get_gsyn_inh: bool,
            record_gsyn_inh_7: bool, record_input_spikes: bool,
            record_input_spikes_7: bool, get_all: bool, get_weights: bool,
            get_delays: bool, new_pop: Literal[False], n_neurons: int,
            cell_class: Type, cell_params: Dict[str, float],
            weight_to_spike: float,
            set_between_runs: List[Tuple[int, str, float]],
            reset: Literal[False]) -> Tuple:
        results = ()

        for runtime in run_times[:-1]:
            # This looks strange but is to allow getting data before run
            if runtime > 0:
                p.run(runtime)
            run_count += 1

            if extract_between_runs:
                if runtime > 0:
                    self._get_data(populations[0], populations[1],
                                   get_spikes, record_7, get_v, record_v_7,
                                   get_gsyn_exc, record_gsyn_exc_7,
                                   get_gsyn_inh, record_gsyn_inh_7,
                                   record_input_spikes, record_input_spikes_7,
                                   get_all)
                self._get_weight_delay(projections[0], get_weights, get_delays)

            if new_pop:
                populations.append(
                    p.Population(
                        n_neurons, cell_class(**cell_params), label='pop_2'))
                injection_connection = [(n_neurons - 1, 0, weight_to_spike, 1)]
                new_projection = p.Projection(
                    populations[0], populations[2],
                    p.FromListConnector(injection_connection),
                    p.StaticSynapse(weight=weight_to_spike, delay=1))
                projections.append(new_projection)

            if spike_times_list is not None:
                populations[1].set(spike_times=spike_times_list[run_count])

            for (pop, name, value) in set_between_runs:
                new_values = {name: value}
                populations[pop].set(**new_values)

            if reset:
                p.reset()

        p.run(run_times[-1])

        return results

    def get_output_pop_gsyn_exc_neo(self) -> neo.block:
        return self._recorded_gsyn_exc_list[0]

    def get_output_pop_gsyn_exc_numpy(self) -> NDArray:
        gsyn_exc_neo = self._recorded_gsyn_exc_list[0]
        return neo_convertor.convert_data(gsyn_exc_neo, "gsyn_exc")

    def get_output_pop_gsyn_exc_list(self) -> List[neo.block]:
        return self._recorded_gsyn_exc_list

    def get_output_pop_gsyn_exc_list_numpy(self) -> List[NDArray]:
        return list(map(
            neo_convertor.convert_gsyn_exc_list,  # type: ignore[arg-type]
            self._recorded_gsyn_exc_list))

    def get_output_pop_gsyn_exc_7(self) -> NDArray[floating]:
        assert self._recorded_gsyn_exc_7 is not None
        return self._recorded_gsyn_exc_7

    def get_output_pop_gsyn_inh_list(self) -> List[neo.block]:
        return self._recorded_gsyn_inh_list

    def get_output_pop_gsyn_inh_list_numpy(self) -> List[NDArray]:
        return list(map(
            neo_convertor.convert_gsyn_inh_list,  # type: ignore[arg-type]
            self._recorded_gsyn_inh_list))

    def get_output_pop_gsyn_inh_neo(self) -> neo.Block:
        return self._recorded_gsyn_inh_list[0]

    def get_output_pop_gsyn_inh_numpy(self) -> NDArray:
        gsyn_inh_neo = self._recorded_gsyn_inh_list[0]
        return neo_convertor.convert_data(gsyn_inh_neo, "gsyn_exc")

    def get_output_pop_gsyn_inh_7(self) -> Optional[NDArray[floating]]:
        return self._recorded_gsyn_inh_7

    def get_output_pop_voltage_list(self) -> List[neo.Block]:
        return self._recorded_v_list

    def get_output_pop_voltage_list_numpy(self) -> List[NDArray[floating]]:
        return list(map(
            neo_convertor.convert_v_list,   # type: ignore[arg-type]
            self._recorded_v_list))

    def get_output_pop_voltage_neo(self) -> neo.Block:
        return self._recorded_v_list[0]

    def get_output_pop_voltage_numpy(self) -> NDArray:
        v_neo = self._recorded_v_list[0]
        return neo_convertor.convert_data(v_neo, "v")

    def get_output_pop_voltage_7(self) -> NDArray[floating]:
        assert self._recorded_v_7 is not None
        return self._recorded_v_7

    def get_output_pop_spikes_list(self) -> List[neo.Block]:
        assert self._recorded_spikes_list is not None
        return self._recorded_spikes_list

    def get_output_pop_spikes_list_numpy(self) -> List[NDArray]:
        return list(map(
            neo_convertor.convert_spikes, self._recorded_spikes_list))

    def get_output_pop_spikes_neo(self) -> neo.Block:
        return self._recorded_spikes_list[0]

    def get_output_pop_spikes_numpy(self) -> NDArray:
        spikes = self._recorded_spikes_list[0]
        return neo_convertor.convert_spikes(spikes)

    def get_output_pop_spikes_7(self) -> NDArray[floating]:
        assert self._recorded_spikes_7 is not None
        return self._recorded_spikes_7

    def get_output_pop_all_list(self) -> List[neo.Block]:
        return self._recorded_all_list

    def get_output_pop_all_neo(self) -> neo.Block:
        return self._recorded_all_list[0]

    def get_spike_source_spikes_list(self) -> List[neo.Block]:
        return self._input_spikes_recorded_list

    def get_spike_source_spikes_list_numpy(self) -> List[NDArray]:
        return list(map(neo_convertor.convert_spikes,
                        self._input_spikes_recorded_list))

    def get_spike_source_spikes_neo(self) -> neo.Block:
        return self._input_spikes_recorded_list[0]

    def get_spike_source_spikes_numpy(self) -> NDArray:
        spikes = self._input_spikes_recorded_list[0]
        return neo_convertor.convert_spikes(spikes)

    def get_spike_source_spikes_7(self) -> Any:
        return self._input_spikes_recorded_7

    def get_weights(self) -> List[ConnectionHolder]:
        """
        List of weights Connectionholders
        """
        return self._weights

    def get_delay(self) -> List[ConnectionHolder]:
        """
        List of delay Connectionholders
        """
        return self._delays

    def _get_data(
            self, output_population: Population, input_population: Population,
            get_spikes: bool, record_7: bool, get_v: bool, record_v_7: bool,
            get_gsyn_exc: bool, record_gsyn_exc_7: bool, get_gsyn_inh: bool,
            record_gysn_inh_7: bool, record_input_spikes: bool,
            record_input_spikes_7: bool, get_all: bool) -> None:

        if get_spikes:
            spikes = output_population.get_data(['spikes'])
            self._recorded_spikes_list.append(spikes)

        if record_7:
            spikes = output_population.spinnaker_get_data('spikes')
            if self._recorded_spikes_7 is None:
                self._recorded_spikes_7 = spikes
            else:
                self._recorded_spikes_7 += spikes

        if get_v:
            self._recorded_v_list.append(output_population.get_data(['v']))

        if record_v_7:
            v = output_population.spinnaker_get_data('v')
            if self._recorded_v_7 is None:
                self._recorded_v_7 = v
            else:
                self._recorded_v_7 += v

        if get_gsyn_exc:
            gsyn_exc = output_population.get_data(['gsyn_exc'])
            self._recorded_gsyn_exc_list.append(gsyn_exc)

        if record_gsyn_exc_7:
            gsyn_exc = output_population.spinnaker_get_data('gsyn_exc')
            if self._recorded_gsyn_exc_7 is None:
                self._recorded_gsyn_exc_7 = gsyn_exc
            else:
                self._recorded_gsyn_exc_7 += gsyn_exc

        if get_gsyn_inh:
            gsyn_inh = output_population.get_data(['gsyn_inh'])
            self._recorded_gsyn_inh_list.append(gsyn_inh)

        if record_gysn_inh_7:
            gsyn_inh = output_population.spinnaker_get_data('gsyn_inh')
            if self._recorded_gsyn_inh_7 is None:
                self._recorded_gsyn_inh_7 = gsyn_inh
            else:
                self._recorded_gsyn_inh_7 += gsyn_inh

        if record_input_spikes:
            spikes = input_population.get_data(['spikes'])
            self._input_spikes_recorded_list.append(spikes)

        if record_input_spikes_7:
            spikes = input_population.spinnaker_get_data('spikes')
            if self._input_spikes_recorded_7 is None:
                self._input_spikes_recorded_7 = spikes
            else:
                self._input_spikes_recorded_7 += spikes

        if get_all:
            self._recorded_all_list.append(output_population.get_data(['all']))

    def _get_weight_delay(self, projection: Projection, get_weights: bool,
                          get_delays: bool) -> None:
        if get_weights:
            weights = projection.get(
                attribute_names=["weight"], format="list", with_address=True)
            self._weights.append(weights)
        if get_delays:
            delays = projection.get(
                attribute_names=["delay"], format="list", with_address=True)
            self._delays.append(delays)


if __name__ == "__main__":
    """
    main entrance method
    """
    blah = SynfireRunner()
    blah.do_run(20)
