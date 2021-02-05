# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import random
import sys
import time
import unittest
from unittest import SkipTest
import numpy
import sqlite3
import spinn_utilities.conf_loader as conf_loader
from spinnman.exceptions import SpinnmanException
from spalloc.job import JobDestroyedError
from spinn_front_end_common.utilities import globals_variables

random.seed(os.environ.get('P8_INTEGRATION_SEED', None))
if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
    max_tries = 3
else:
    max_tries = 1


def calculate_stdp_times(pre_spikes, post_spikes, plastic_delay):
    # If no post spikes, no changes
    if len(post_spikes) == 0:
        return numpy.zeros(0), numpy.zeros(0)

    # Get the spikes and time differences that will be considered by
    # the simulation (as the last pre-spike will be considered differently)
    last_pre_spike_delayed = pre_spikes[-1] - plastic_delay
    considered_post_spikes = post_spikes[post_spikes < last_pre_spike_delayed]
    if len(considered_post_spikes) == 0:
        return numpy.zeros(0), numpy.zeros(0)
    potentiation_time_diff = numpy.ravel(numpy.subtract.outer(
        considered_post_spikes + plastic_delay, pre_spikes[:-1]))
    potentiation_times = (
        potentiation_time_diff[potentiation_time_diff > 0] * -1)
    depression_time_diff = numpy.ravel(numpy.subtract.outer(
        considered_post_spikes + plastic_delay, pre_spikes))
    depression_times = depression_time_diff[depression_time_diff < 0]
    return potentiation_times, depression_times


def calculate_spike_pair_additive_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, max_weight,
        a_plus, a_minus, tau_plus, tau_minus):
    """ Calculates the expected stdp weight for SpikePair Additive STDP
    """
    potentiation_times, depression_times = calculate_stdp_times(
        pre_spikes, post_spikes, plastic_delay)

    # Work out the weight according to the additive rule
    potentiations = max_weight * a_plus * numpy.exp(
        (potentiation_times / tau_plus))
    depressions = max_weight * a_minus * numpy.exp(
        (depression_times / tau_minus))
    return initial_weight + numpy.sum(potentiations) - numpy.sum(depressions)


def calculate_spike_pair_multiplicative_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, min_weight,
        max_weight, a_plus, a_minus, tau_plus, tau_minus):
    """ Calculates the expected stdp weight for SpikePair Multiplicative STDP
    """
    potentiation_times, depression_times = calculate_stdp_times(
        pre_spikes, post_spikes, plastic_delay)

    # Work out the weight according to the multiplicative rule
    potentiations = (max_weight - initial_weight) * a_plus * numpy.exp(
        (potentiation_times / tau_plus))
    depressions = (initial_weight - min_weight) * a_minus * numpy.exp(
        (depression_times / tau_minus))
    return initial_weight + numpy.sum(potentiations) - numpy.sum(depressions)


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # Remove random effect for testing
        # Set test_seed to None to allow random
        self._test_seed = 1

        globals_variables.unset_simulator()
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)

    def assert_logs_messages(
            self, log_records, sub_message, log_level='ERROR', count=1,
            allow_more=False):
        """ Tool to assert the log messages contain the sub-message
        :param log_records: list of log message
        :param sub_message: text to look for
        :param log_level: level to look for
        :param count: number of times this message should be found
        :param allow_more: If True, OK to have more than count repeats
        :return: None
        """
        seen = 0
        for record in log_records:
            if record.levelname == log_level and \
                    sub_message in str(record.msg):
                seen += 1
        if allow_more and seen > count:
            return
        if seen != count:
            raise self.failureException(
                "\"{}\" not found in any {} logs {} times, was found {} "
                "times".format(sub_message, log_level, count, seen))

    def assert_not_spin_three(self):
        config = conf_loader.load_config(
            filename="spynnaker.cfg", defaults=[])
        if config.has_option("Machine", "version"):
            version = config.get("Machine", "version")
            if version in ["2", "3"]:
                raise SkipTest(
                    "This test will not run on a spin {} board".format(
                        version))

    def report(self, message, file_name):
        if not message.endswith("\n"):
            message += "\n"
        p8_integration_tests_directory = os.path.dirname(__file__)
        test_dir = os.path.dirname(p8_integration_tests_directory)
        report_dir = os.path.join(test_dir, "reports")
        if not os.path.exists(report_dir):
            # It might now exist if run in parallel
            try:
                os.makedirs(report_dir)
            except Exception:
                pass
        report_path = os.path.join(report_dir, file_name)
        with open(report_path, "a") as report_file:
            report_file.write(message)

    def get_provenance(self, _main_name, detail_name):
        provenance_file_path = globals_variables.get_simulator() \
            ._provenance_file_path
        prov_file = os.path.join(provenance_file_path, "provenance.sqlite3")
        prov_db = sqlite3.connect(prov_file)
        prov_db.row_factory = sqlite3.Row
        results = []
        for row in prov_db.execute(
                "SELECT description_name AS description, the_value AS 'value' "
                "FROM provenance_view WHERE source_name = 'pacman' AND "
                "description_name LIKE ?", ("%" + detail_name, )):
            results.append("{}: {}\n".format(row["description"], row["value"]))
        return "".join(results)

    def get_provenance_files(self):
        provenance_file_path = (
            globals_variables.get_simulator()._provenance_file_path)
        return os.listdir(provenance_file_path)

    def get_system_iobuf_files(self):
        system_iobuf_file_path = (
            globals_variables.get_simulator()._system_provenance_file_path)
        return os.listdir(system_iobuf_file_path)

    def get_app_iobuf_files(self):
        app_iobuf_file_path = (
            globals_variables.get_simulator()._app_provenance_file_path)
        return os.listdir(app_iobuf_file_path)

    def get_run_time_of_BufferExtractor(self):
        return self.get_provenance("Execution", "BufferExtractor")

    def known_issue(self, issue):
        self.report(issue, "Skipped_due_to_issue")
        raise SkipTest(issue)

    def destory_path(self):
        p8_integration_tests_directory = os.path.dirname(__file__)
        test_dir = os.path.dirname(p8_integration_tests_directory)
        return os.path.join(test_dir, "JobDestroyedError.txt")

    def spinnman_exception_path(self):
        p8_integration_tests_directory = os.path.dirname(__file__)
        test_dir = os.path.dirname(p8_integration_tests_directory)
        return os.path.join(test_dir, "JobDestroyedError.txt")

    def runsafe(self, method, retry_delay=3.0):
        retries = 0
        while True:
            try:
                method()
                break
            except JobDestroyedError as ex:
                class_file = sys.modules[self.__module__].__file__
                with open(self.destory_path(), "a") as destroyed_file:
                    destroyed_file.write(class_file)
                    destroyed_file.write("\n")
                    destroyed_file.write(str(ex))
                    destroyed_file.write("\n")
                retries += 1
                globals_variables.unset_simulator()
                if retries >= max_tries:
                    raise
            except SpinnmanException as ex:
                class_file = sys.modules[self.__module__].__file__
                with open(self.spinnman_exception_path(), "a") as exc_file:
                    exc_file.write(class_file)
                    exc_file.write("\n")
                    exc_file.write(str(ex))
                    exc_file.write("\n")
                retries += 1
                globals_variables.unset_simulator()
                if retries >= max_tries:
                    raise
            print("")
            print("==========================================================")
            print(" Will run {} again in {} seconds".format(
                method, retry_delay))
            print("retry: {}".format(retries))
            print("==========================================================")
            print("")
            time.sleep(retry_delay)

    def get_placements(self, label):
        report_default_directory = globals_variables.get_simulator() \
            ._report_default_directory
        placement_path = os.path.join(
            report_default_directory, "placement_by_vertex_using_graph.rpt")
        placements = []
        in_core = False
        with open(placement_path, "r") as placement_file:
            for line in placement_file:
                if in_core:
                    if "**** Vertex: '" in line:
                        in_core = False
                    elif "on core (" in line:
                        all = line[line.rfind("(")+1: line.rfind(")")]
                        [x, y, p] = all.split(",")
                        placements.append([x.strip(), y.strip(), p.strip()])
                if line == "**** Vertex: '" + label + "'\n":
                    in_core = True
        return placements
