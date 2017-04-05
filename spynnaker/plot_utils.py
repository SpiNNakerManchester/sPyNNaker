# Imports
import numpy as np
import matplotlib.pyplot as plt


def line_plot(data, title=None):
    if data is None or len(data) == 0:
        if title is None:
            print "NO Data"
        else:
            print "NO data for " + title
        return
    print ("Setting up line graph")
    neurons = np.unique(data[:, 0])
    for neuron in neurons:
        time = [i[1] for i in data if i[0] == neuron]
        membrane_voltage = [i[2] for i in data if i[0] == neuron]
        plt.plot(time, membrane_voltage)
    plt.xlabel("Time (ms)")
    plt.ylabel("Neuron")
    if title is not None:
        plt.title(title)

    min_data = min(data[:, 2])
    max_data = max(data[:, 2])
    adjust = (max_data - min_data) * 0.1
    plt.axis([min(data[:, 1]), max(data[:, 1]), min_data - adjust,
              max_data + adjust])
    plt.show()


def heat_plot(data, ylabel=None, title=None):
    if data is None or len(data) == 0:
        if title is None:
            print "NO Data"
        else:
            print "NO data for " + title
        return
    print "Setting up heat graph"
    neurons = data[:, 0].astype(int)
    times = data[:, 1].astype(int)
    info = data[:, 2]
    info_array = np.empty((max(neurons)+1, max(times)+1))
    info_array[:] = np.nan
    info_array[neurons, times] = info
    plt.xlabel("Time (ms)")
    plt.ylabel("Neuron")
    if title is not None:
        plt.title(title)
    plt.imshow(info_array, cmap='hot', interpolation='bilinear', aspect='auto')
    plt.colorbar()
    plt.show()


def plot_spikes(spikes, spikes2=None, spikes3=None, title="spikes"):
    """

    :param spikes: Numpy array of spikes
    :param spikes2: Optional: Numport array of spikes
    :param spikes3: Optional: Numport array of spikes
    """
    found = False
    minTime = None
    maxTime = None
    minSpike = None
    maxSpike = None
    spike_time = [i[1] for i in spikes]
    spike_id = [i[0] for i in spikes]
    if len(spike_time) == 0:
        print "No spikes detected"
    else:
        found = True
        minTime = min(spike_time)
        maxTime = max(spike_time)
        minSpike = min(spike_id)
        maxSpike = max(spike_id)
        plt.plot(spike_time, spike_id, "b.",)
    if spikes2 is not None:
        spike_time = [i[1] for i in spikes2]
        spike_id = [i[0] for i in spikes2]
        if len(spike_time) == 0:
            print "No spikes detected in second spike data"
        else:
            found = True
            minTime = min(minTime, min(spike_time))
            maxTime = max(maxTime, max(spike_time))
            minSpike = min(minSpike, min(spike_id))
            maxSpike = max(maxSpike, max(spike_id))
            plt.plot(spike_time, spike_id, "r.", )
    if spikes3 is not None:
        spike_time = [i[1] for i in spikes3]
        spike_id = [i[0] for i in spikes3]
        if len(spike_time) == 0:
            print "No spikes detected in third spike data"
        else:
            found = True
            minTime = min(minTime, min(spike_time))
            maxTime = max(maxTime, max(spike_time))
            minSpike = min(minSpike, min(spike_id))
            maxSpike = max(maxSpike, max(spike_id))
            plt.plot(spike_time, spike_id, "g.", )
    if found:
        plt.xlabel("Time (ms)")
        plt.ylabel("Neuron ID")
        plt.title(title)
        timeDiff = (maxTime - minTime) * 0.05
        minTime = minTime - timeDiff
        maxTime = maxTime + timeDiff
        spikeDiff = (maxSpike - minSpike) * 0.05
        minSpike = minSpike - spikeDiff
        maxSpike = maxSpike + spikeDiff
        plt.axis([minTime, maxTime, minSpike, maxSpike])
        plt.show()


if __name__ == "__main__":
    spikes = np.loadtxt("spikes.csv", delimiter=',')
    plot_spikes(spikes)
    import spynnaker.spike_checker as spike_checker
    spike_checker.synfire_multiple_lines_spike_checker(spikes, 200, 5)
