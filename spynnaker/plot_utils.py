# Imports
import numpy as np
import sys

try:
    import matplotlib.pyplot as plt
    matplotlib_missing = False
except Exception as e:
    matplotlib_missing = True


def _precheck(data, title):
    if data is None or len(data) == 0:
        if title is None:
            print "NO Data"
        else:
            print "NO data for " + title
        return False
    if matplotlib_missing:
        if title is None:
            print "matplotlib not installed skipping plotting"
        else:
            print "matplotlib not installed skipping plotting for " + title
        return False
    return True


def line_plot(data, title=None):
    if not _precheck(data, title):
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
    if not _precheck(data, title):
        return
    print "Setting up heat graph"
    neurons = data[:, 0].astype(int)
    times = data[:, 1].astype(int)
    info = data[:, 2]
    info_array = np.empty((max(neurons)+1, max(times)+1))
    info_array[:] = np.nan
    info_array[neurons, times] = info
    plt.xlabel("Time (ms)")
    plt.ylabel(ylabel)
    if title is not None:
        plt.title(title)
    plt.imshow(info_array, cmap='hot', interpolation='bilinear', aspect='auto')
    plt.colorbar()
    plt.show()


def get_colour():
    yield "b."
    yield "g."
    yield "r."
    yield "c."
    yield "m."
    yield "y."
    yield "k."


def plot_spikes(spikes, spikes2=None, spikes3=None, title="spikes"):
    """

    :param spikes: Numpy array of spikes
    :param spikes2: Optional: Numport array of spikes
    :param spikes3: Optional: Numport array of spikes
    """
    if not _precheck(spikes, title):
        return

    if isinstance(spikes, np.ndarray):
        spikes = [spikes]

    colours = get_colour()

    minTime = sys.maxint
    maxTime = 0
    minSpike = sys.maxint
    maxSpike = 0

    print "Plotiing {} set of sapikes".format(len(spikes))
    for single_spikes in spikes:
        spike_time = [i[1] for i in single_spikes]
        spike_id = [i[0] for i in single_spikes]
        minTime = min(minTime, min(spike_time))
        maxTime = max(maxTime, max(spike_time))
        minSpike = min(minSpike, min(spike_id))
        maxSpike = max(maxSpike, max(spike_id))
        plt.plot(spike_time, spike_id, colours.next(), )
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

# This is code for manual testing.
if __name__ == "__main__":
    spikes = np.loadtxt("spikes.csv", delimiter=',')
    plot_spikes(spikes)
    double = np.loadtxt("spikes.csv", delimiter=',')
    for i in range(len(double)):
        double[i][0] = double[i][0] + 5
    plot_spikes([spikes, double])
