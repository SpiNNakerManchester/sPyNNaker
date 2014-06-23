__author__ = 'stokesa6'
from neural_spinnaker.visualiser_pages.plotter.plotter import Plotter as Plot
from pycha import scatter


class MyScatterChart(scatter.ScatterplotChart):
    
    def _getDatasetsKeys(self):
        """Return the name of each data set"""
        return [d[0] for d in reversed(self.datasets)]


#class required to make a scatter plot (currently what the raster is)
class ScatterplotChart(Plot):

    def __init__(self):
        Plot.__init__(self)
        self.chart = None
        self._data = ()

    def set_data(self, data, key):
        """
        Update plot's data and refreshes DrawingArea contents. Data must be a
        list containing a set of x and y values.
        """

        self._data = self._data + ((data, key),)
        self.queue_draw()

    def plot(self):
        """
        Initializes chart (if needed), set data and plots.
        """
        self.chart = MyScatterChart(self._surface, self._options)
        #self.clean()
        self.chart.addDataset(self._data)
        self.chart.render()

    def replot(self):
        self.chart.render()
        self.chart.update()

    def clean(self):
        self.chart.clean()

