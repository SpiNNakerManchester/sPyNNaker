import numpy
from .spike_source_array import SpikeSourceArray
from spynnaker.pyNN.utilities import utility_calls


class SpikeSourceFromFile(SpikeSourceArray):
    """ SpikeSourceArray that works from a file
    """

    def __init__(
            self, spike_time_file, min_atom=None, max_atom=None, min_time=None,
            max_time=None, split_value="\t"):
        # pylint: disable=too-many-arguments, too-many-locals
        spike_times = utility_calls.read_spikes_from_file(
            spike_time_file, min_atom, max_atom, min_time, max_time,
            split_value)
        super(SpikeSourceFromFile, self).__init__(spike_times)

    @staticmethod
    def _subsample_spikes_by_time(spike_array, start, stop, step):
        sub_sampled_array = {}
        for neuron in spike_array:
            times = [t for t in spike_array[neuron] if start <= t < stop]
            interval = step // 2
            t_start = times[0]
            t_last = len(times)
            t_index = 0
            spikes_in_interval = 0
            subsampled_times = []
            while t_index < t_last:
                spikes_in_interval = 0
                while (t_index < t_last and
                        times[t_index] <= t_start + interval):
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
    def _convert_spike_list_to_timed_spikes(
            spike_list, min_idx, max_idx, tmin, tmax, tstep):
        # pylint: disable=too-many-arguments
        times = numpy.array(range(tmin, tmax, tstep))
        spike_ids = sorted(spike_list)
        possible_neurons = range(min_idx, max_idx)
        spike_array = dict([(neuron, times) for neuron in spike_ids
                            if neuron in possible_neurons])
        return spike_array

    @property
    def spike_times(self):
        return self._spike_times
