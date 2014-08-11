from spynnaker.pyNN.utilities.conf import config

from pacman.utilities.report_states import ReportState as PacmanReportState


class ReportState(object):

    def __init__(self):
        self._partitioner_report = \
            config.getboolean("Reports", "writePartitionerReports")
        self._placer_report = \
            config.getboolean("Reports", "writePlacerReports")
        self._router_report = \
            config.getboolean("Reports", "writeRouterReports")
        self._router_dat_based_report = \
            config.getboolean("Reports", "writeRouterDatReport")
        self._routing_info_report = \
            config.getboolean("Reports", "writeRouterInfoReport")
        self._data_spec_report = \
            config.getboolean("Reports", "writeTextSpecs")
        self._write_reload_steps = \
            config.getboolean("Reports", "writeReloadSteps")
        self._generate_time_recordings_for_performance_measurements = \
            config.getboolean("Reports", "outputTimesForSections")
        self._transciever_report = \
            config.getboolean("Reports", "writeTransceiverReport")

    @property
    def partitioner_report(self):
        return self._partitioner_report

    @property
    def placer_report(self):
        return self._placer_report

    @property
    def router_report(self):
        return self._router_report

    @property
    def router_dat_based_report(self):
        return self._router_dat_based_report

    @property
    def routing_info_report(self):
        return self._routing_info_report

    @property
    def data_spec_report(self):
        return self._data_spec_report

    @property
    def write_reload_steps(self):
        return self._write_reload_steps

    @property
    def transciever_report(self):
        return self._transciever_report

    @property
    def generate_time_recordings_for_performance_measurements(self):
        return self._generate_time_recordings_for_performance_measurements

    def generate_pacman_report_states(self):
        return PacmanReportState(
            self._partitioner_report, self._placer_report, self._router_report,
            self._router_dat_based_report, self._routing_info_report)

