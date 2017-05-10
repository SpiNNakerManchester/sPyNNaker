import unittest
import os
import shutil

from spynnaker.pyNN.spinnaker import Spinnaker
from spynnaker.pyNN.utilities import conf
from spinn_utilities.helpful_functions import set_up_report_specifics


class TestCFGs(unittest.TestCase):

    def setUp(self):
        self._previous_reportsEnabled = conf.config.get(
            "Reports", "reportsEnabled")
        self.previous_defaultReportFilePath = conf.config.get(
            "Reports", "defaultReportFilePath")

    def tearDown(self):
        conf.config.set("Reports", "defaultReportFilePath",
                        self.previous_defaultReportFilePath)
        conf.config.set("Reports", "reportsEnabled",
                        self._previous_reportsEnabled)

    @unittest.skip("broken")
    def test_reports_creation_custom_location(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        conf.config.set("Reports", "defaultReportFilePath", current_path)
        conf.config.set("Reports", "reportsEnabled", "True")
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)

        if 'reports' in os.listdir(current_path):
            shutil.rmtree(os.path.join(current_path, 'reports'))
        set_up_report_specifics()

        self.assertEqual(spinn._report_default_directory,
                         os.path.join(current_path, 'reports', 'latest'))
        # File reports should be in the new location
        self.assertIn('reports', os.listdir(current_path))

    def test_set_up_main_objects(self):
        Spinnaker(timestep=1, min_delay=1, max_delay=10)


if __name__ == '__main__':
    unittest.main()
