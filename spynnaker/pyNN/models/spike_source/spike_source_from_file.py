"""
SpikeSourceFromFile
"""

# spynnaker imports
from spynnaker.pyNN.models.spike_source.spike_source_array import \
    SpikeSourceArray

# general imports
import numpy
import itertools

class SpikeSourceFromFile(SpikeSourceArray):
    """
    helper class that allows spikes froma  file to be read in and added to a
    buffered spike soruce
    """

    def __init__(
            self, n_neurons, spike_time_file, machine_time_step,
            spikes_per_second, ring_buffer_sigma, timescale_factor, port=None,
            tag=None, ip_address=None, board_address=None, min_atom=None,
            max_atom=None, min_time=None, max_time=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=None,
            constraints=None, label="SpikeSourceArray"):

        spike_times = self._read_spikes_from_file(
            spike_time_file, min_atom, max_atom, min_time, max_time,
            machine_time_step)

        SpikeSourceArray.__init__(
            self, n_neurons, spike_times, machine_time_step,
            spikes_per_second, ring_buffer_sigma, timescale_factor, port=port,
            tag=tag, ip_address=ip_address, board_address=board_address,
            max_on_chip_memory_usage_for_spikes_in_bytes=
            max_on_chip_memory_usage_for_spikes_in_bytes,
            constraints=constraints, label=label)

    @staticmethod
    def _read_spikes_from_file(
            spike_time_file, min_atom, max_atom, min_time, max_time,
            machine_time_step):
        """

        :param spike_time_file:
        :param min_atom:
        :param max_atom:
        :param min_time:
        :param max_time:
        :param machine_time_step:
        :return:
        """
        spike_times = list()
        spike_ids = list()
        with open(spike_time_file, 'r') as fsource:
                read_data = fsource.readlines()

        for line in read_data:
            if not line.startswith('#'):
                values = line.split("\t")
                neuron_id = int(eval(values[1]))
                time = float(eval(values[0]))
                if (min_atom <= neuron_id < max_atom and
                        min_time <= time < max_time):
                    spike_times.append(time)
                    spike_ids.append(neuron_id)
                else:
                    print "failed to enter {}:{}".format(neuron_id, time)

        result = numpy.dstack((spike_ids, spike_times))[0]
        result = result[numpy.lexsort((spike_times, spike_ids))]
        return result

    @staticmethod
    def _subsample_spikes_by_time(spike_array, start, stop, step):
        """

        :param spike_array:
        :param start:
        :param stop:
        :param step:
        :return:
        """
        sub_sampled_array = {}
        for neuron in spike_array:
            times = [t for t in spike_array[neuron] if start <= t < stop]
            interval = step / 2
            t_start = times[0]
            t_last = len(times)
            t_index = 0
            spikes_in_interval = 0
            subsampled_times = []
            while t_index < t_last:
                spikes_in_interval = 0
                while t_index < t_last and times[t_index] <= t_start + interval:
                    spikes_in_interval += 1
                    if spikes_in_interval >= interval:
                        t_start = times[t_index] + interval
                        subsampled_times.append(times[t_index])
                        try:
                            t_index = next(i for i in range(t_index, t_last)
                                           if times[i] >= t_start)
                        except StopIteration:
                            t_index = t_last
                            break
                        t_index += 1
                    else:
                        t_start = t_index
            sub_sampled_array[neuron] = subsampled_times
        return sub_sampled_array

    @staticmethod
    def _convert_spike_list_to_timed_spikes(spike_list, min_idx, max_idx,
                                            tmin, tmax, tstep):
        """

        :param spike_list:
        :param min_idx:
        :param max_idx:
        :param tmin:
        :param tmax:
        :param tstep:
        :return:
        """
        times = numpy.array(range(tmin, tmax, tstep))
        spike_ids = sorted(spike_list)
        possible_neurons = range(min_idx, max_idx)
        spike_array = dict([(neuron, times) for neuron in spike_ids
                            if neuron in possible_neurons])
        return spike_array

    @property
    def spike_times(self):
        """
        helper method for acquiring the spike times
        :return:
        """
        return self._spike_times