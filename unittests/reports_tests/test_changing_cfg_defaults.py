import unittest
from spynnaker.pyNN.spinnaker import Spinnaker
import os
from spynnaker.pyNN.utilities import conf
import spynnaker.pyNN.exceptions as exceptions
import time
import shutil


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

    def test_reports_creation_custom_location(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        conf.config.set("Reports", "defaultReportFilePath", current_path)
        conf.config.set("Reports", "reportsEnabled", "True")
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)

        if 'reports' in os.listdir(current_path):
            shutil.rmtree(os.path.join(current_path,'reports'))
        spinn._set_up_report_specifics()

        self.assertEqual(spinn._report_default_directory,
                os.path.join(current_path,'reports', 'latest'))
        if 'reports' not in os.listdir(current_path):
            raise AssertionError("File reports should be in the new location")

    def test_set_up_main_objects(self):
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)
        self.assertEqual(spinn._app_id, conf.config.getint("Machine", "appID"))


if __name__ == '__main__':
    unittest.main()
