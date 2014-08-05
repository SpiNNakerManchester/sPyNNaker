"""
class to contain visulaiser paramters for a given vertex
"""


class VisualiserVertex(object):

    def __init__(self, visualiser_mode, visualiser_2d_dimensions,
                 visualiser_no_colours, visualiser_average_period_tics,
                 visualiser_longer_period_tics,
                 visualiser_update_screen_in_tics,
                 visualiser_reset_counters,
                 visualiser_reset_counter_period,
                 visualiser_raster_separate, vertex):
        self._visualiser_mode = visualiser_mode
        #topological views
        self._visualiser_2d_dimensions = visualiser_2d_dimensions
        self._visualiser_no_colours = visualiser_no_colours
        self._visualiser_average_period_tics = visualiser_average_period_tics
        self._visualiser_longer_period_tics = visualiser_longer_period_tics
        self._visualiser_update_screen_in_tics = \
            visualiser_update_screen_in_tics
        self._visualiser_reset_counters = visualiser_reset_counters
        self._visualiser_reset_counter_period = visualiser_reset_counter_period
        #raster views
        self._visualiser_raster_separate = visualiser_raster_separate
        self._vertex = vertex

    @property
    def visualiser_mode(self):
        return self._visualiser_mode

    @property
    def visualiser_2d_dimensions(self):
        return self._visualiser_2d_dimensions

    @property
    def visualiser_no_colours(self):
        return self._visualiser_no_colours

    @property
    def visualiser_average_period_tics(self):
        return self._visualiser_average_period_tics

    @property
    def visualiser_longer_period_tics(self):
        return self._visualiser_longer_period_tics

    @property
    def visualiser_update_screen_in_tics(self):
        return self._visualiser_update_screen_in_tics

    @property
    def visualiser_reset_counters(self):
        return self._visualiser_reset_counters

    @property
    def visualiser_reset_counter_period(self):
        return self._visualiser_reset_counter_period

    @property
    def visualiser_raster_separate(self):
        return self._visualiser_raster_separate

    @property
    def vertex(self):
        return self._vertex
