import unittest
from spynnaker.pyNN.visualiser_package.visualiser_vertex import VisualiserVertex
import spynnaker.pyNN.utilities.constants as constant
from pacman.model.graph.vertex import Vertex


class TestVisualiserVertex(unittest.TestCase):
    def setUp(self):
        self._visualiser_mode = constant.VISUALISER_MODES.RASTER.value
        #topological views
        self._visualiser_2d_dimensions = (2,3)
        self._visualiser_no_colours = 256
        self._visualiser_average_period_tics = 11
        self._visualiser_longer_period_tics = 34
        self._visualiser_update_screen_in_tics = \
            100
        self._visualiser_reset_counters = 5
        self._visualiser_reset_counter_period = 50
        #raster views
        self._visualiser_raster_separate = 14
        self._vertex = Vertex(10,"Test vertex")
        self.visualiser_vertex = VisualiserVertex(
            self._visualiser_mode,
            self._visualiser_2d_dimensions,
            self._visualiser_no_colours,
            self._visualiser_average_period_tics,
            self._visualiser_longer_period_tics,
            self._visualiser_update_screen_in_tics,
            self._visualiser_reset_counters,
            self._visualiser_reset_counter_period,
            self._visualiser_raster_separate,
            self._vertex
            )

    def test_visualiser_mode(self):
        self.assertEqual(self.visualiser_vertex.visualiser_mode, self._visualiser_mode)

    def test_visualiser_2d_dimensions(self):
        self.assertEqual(self.visualiser_vertex.visualiser_2d_dimensions, self._visualiser_2d_dimensions)

    def test_visualiser_no_colours(self):
        self.assertEqual(self.visualiser_vertex.visualiser_no_colours, self._visualiser_no_colours)

    def test_visualiser_average_period_tics(self):
        self.assertEqual(self.visualiser_vertex.visualiser_average_period_tics, self._visualiser_average_period_tics)

    def test_visualiser_longer_period_tics(self):
        self.assertEqual(self.visualiser_vertex.visualiser_longer_period_tics, self._visualiser_longer_period_tics)

    def test_visualiser_update_screen_in_tics(self):
        self.assertEqual(self.visualiser_vertex.visualiser_update_screen_in_tics, self._visualiser_update_screen_in_tics)

    def test_visualiser_reset_counters(self):
        self.assertEqual(self.visualiser_vertex.visualiser_reset_counters, self._visualiser_reset_counters)

    def test_visualiser_reset_counter_period(self):
        self.assertEqual(self.visualiser_vertex.visualiser_reset_counter_period, self._visualiser_reset_counter_period)

    def test_visualiser_raster_separate(self):
        self.assertEqual(self.visualiser_vertex.visualiser_raster_separate, self._visualiser_raster_separate)

    def test_vertex(self):
        self.assertEqual(self.visualiser_vertex.vertex, self._vertex)


if __name__ == '__main__':
    unittest.main()
