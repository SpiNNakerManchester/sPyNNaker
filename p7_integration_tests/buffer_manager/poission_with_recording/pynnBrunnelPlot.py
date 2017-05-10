'''
    Some plotting functions I stole from the pyNest library :)
'''
import numpy


def _histogram(a, bins=10, plot_range=None, normed=False):

    from numpy import asarray, iterable, linspace, sort, concatenate

    a = asarray(a).ravel()

    if plot_range is not None:
        mn, mx = plot_range
        if mn > mx:
            raise AttributeError(
                "max must be larger than min in range parameter.")

    if not iterable(bins):
        if plot_range is None:
            plot_range = (a.min(), a.max())
        mn, mx = [mi + 0.0 for mi in plot_range]
        if mn == mx:
            mn -= 0.5
            mx += 0.5
        bins = linspace(mn, mx, bins, endpoint=False)
    else:
        if(bins[1:] - bins[:-1] < 0).any():
            raise AttributeError("bins must increase monotonically.")

    # best block size probably depends on processor cache size
    block = 65536
    n = sort(a[:block]).searchsorted(bins)
    for i in xrange(block, a.size, block):
        n += sort(a[i:i + block]).searchsorted(bins)
    n = concatenate([n, [len(a)]])
    n = n[1:] - n[:-1]

    if normed:
        db = bins[1] - bins[0]
        return 1.0 / (a.size * db) * n
    else:
        return n


def _make_plot(ts, ts1, gids, neurons, hist, hist_binwidth, grayscale, title,
               xlabel=None, total_time=None, n_neurons=None):
    """
    Generic plotting routine that constructs a raster plot along with
    an optional histogram (common part in all routines above)
    """
    import pylab  # deferred so unittest are not dependent on it

    pylab.figure()

    if grayscale:
        color_marker = ".k"
        color_bar = "gray"
    else:
        color_marker = "."
        color_bar = "blue"

    color_edge = "black"

    if xlabel is None:
        xlabel = "Time (ms)"

    ylabel = "Neuron ID"

    if hist:
        ax1 = pylab.axes([0.1, 0.3, 0.85, 0.6])
        plotid = pylab.plot(ts1, gids, color_marker)
        pylab.ylabel(ylabel)
        pylab.xticks([])
        if total_time is not None:
            pylab.xlim(0, total_time)
        if n_neurons is not None:
            pylab.ylim(0, n_neurons)

        xlim = pylab.xlim()

        pylab.axes([0.1, 0.1, 0.85, 0.17])
        t_bins = numpy.arange(numpy.amin(ts), numpy.amax(ts),
                              float(hist_binwidth))
        n = _histogram(ts, bins=t_bins)
        num_neurons = len(numpy.unique(neurons))
        heights = 1000 * n / (hist_binwidth * num_neurons)
        pylab.bar(t_bins, heights, width=hist_binwidth, color=color_bar,
                  edgecolor=color_edge)
        pylab.yticks(map(lambda x: int(x),
                         numpy.linspace(0.0, int(max(heights) * 1.1) + 5, 4)))
        pylab.ylabel("Rate (Hz)")
        pylab.xlabel(xlabel)
        pylab.xlim(xlim)
        pylab.axes(ax1)
    else:
        plotid = pylab.plot(ts1, gids, color_marker)
        pylab.xlabel(xlabel)
        pylab.ylabel(ylabel)
        if total_time is not None:
            pylab.xlim(0, total_time)
        if n_neurons is not None:
            pylab.ylim(0, n_neurons)

    if title is None:
        pylab.title("Raster plot")
    else:
        pylab.title(title)

    pylab.draw()

    return plotid


def sortByID(spinnakerMembrane):
    '''
    '''
    memArray = (spinnakerMembrane)
    memIndex = numpy.lexsort((memArray[:, 0], memArray[:, 1]))
    memArraySorted = memArray[memIndex]
    return memArraySorted
