import unittest
from spynnaker.pyNN.spinnaker import Spinnaker
import os
from spynnaker.pyNN.utilities import conf
import spynnaker.pyNN.exceptions as exceptions


class TestCFGs(unittest.TestCase):
    def setUp(self):
        self._previous_reportsEnabled = conf.config.get("Reports", "reportsEnabled")
        self.previous_defaultReportFilePath = conf.config.get("Reports", "defaultReportFilePath")


    def tearDown(self):
        conf.config.set("Reports", "defaultReportFilePath", self.previous_defaultReportFilePath)
        conf.config.set("Reports", "reportsEnabled", self._previous_reportsEnabled)


    def test_reports_creation_default(self):
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)

        conf.config.set("Reports", "defaultReportFilePath", "DEFAULT")
        conf.config.set("Reports", "reportsEnabled", "True")
        exceptions_path = \
                os.path.abspath(exceptions.__file__)
        directory = \
            os.path.abspath(os.path.join(exceptions_path,
                                         os.pardir, os.pardir, os.pardir))

        if 'reports' in os.listdir(directory):
            os.rmdir(os.path.join(directory,'reports'))

        spinn._set_up_report_specifics()
        if 'reports' not in os.listdir(directory):
            raise AssertionError("File reports should be in the default location")

    def test_reports_creation_custom_location(self):
        current_path = os.path.abspath(os.curdir)
        conf.config.set("Reports", "defaultReportFilePath", current_path)
        conf.config.set("Reports", "reportsEnabled", "True")
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)
        exceptions_path = \
                os.path.abspath(exceptions.__file__)
        directory = \
            os.path.abspath(os.path.join(exceptions_path,
                                         os.pardir, os.pardir, os.pardir))


        if 'reports' in os.listdir(directory):
            os.rmdir(os.path.join(directory,'reports'))

        if 'reports' in os.listdir(current_path):
            os.rmdir(os.path.join(current_path,'reports'))
        spinn._set_up_report_specifics()

        self.assertEqual(spinn._report_default_directory, os.path.join(current_path,'reports'))
        if 'reports' not in os.listdir(current_path):
            raise AssertionError("File reports should be in the new location")

    def test_set_up_main_objects(self):
        spinn = Spinnaker(timestep=1, min_delay=1, max_delay=10)
        self.assertEqual(spinn._app_id, conf.config.getint("Machine", "appID"))


if __name__ == '__main__':
    unittest.main()
