import unittest

from spynnaker.pyNN.utilities.conf import config
from spinn_front_end_common.utilities.report_states import ReportState


class TestReportStates(unittest.TestCase):
    def test_partitioner_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.partitioner_report,config.getboolean(
            "Reports", "writePartitionerReports"))

    def test_placer_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.placer_report,config.getboolean(
            "Reports", "writePlacerReports"))

    def test_router_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.router_report,config.getboolean(
            "Reports", "writeRouterReports"))

    def test_router_dat_based_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.router_dat_based_report,config.getboolean(
            "Reports", "writeRouterDatReport"))

    def test_routing_info_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.routing_info_report,config.getboolean(
            "Reports", "writeRouterInfoReport"))

    def test_data_spec_report(self):
        report_state = ReportState()
        self.assertEqual(report_state.data_spec_report,config.getboolean(
            "Reports", "writeTextSpecs"))

    def test_write_reload_steps(self):
        report_state = ReportState()
        self.assertEqual(report_state.write_reload_steps,config.getboolean(
            "Reports", "writeReloadSteps"))

    def test_generate_pacman_report_states(self):
        report_state = ReportState()
        pacman_report_state = \
            report_state.generate_pacman_report_states()
        self.assertEqual(report_state.partitioner_report,
                         pacman_report_state.partitioner_report)
        self.assertEqual(report_state.placer_report,
                         pacman_report_state.placer_report)
        self.assertEqual(report_state.router_report,
                         pacman_report_state.router_report)
        self.assertEqual(report_state.router_dat_based_report,
                         pacman_report_state.router_dat_based_report)
        self.assertEqual(report_state.routing_info_report,
                         pacman_report_state.routing_info_report)

    def test_generate_time_recordings_for_performance_measurements(self):
        report_state = ReportState()
        self.assertEqual(
            report_state.generate_time_recordings_for_performance_measurements,
            config.getboolean("Reports", "outputTimesForSections"))




if __name__ == '__main__':
    unittest.main()
