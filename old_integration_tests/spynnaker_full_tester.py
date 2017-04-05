"""
tester that explores all the config params
"""

from spynnaker.pyNN.utilities.conf import config

import os
import shutil
import subprocess
import copy
import argparse  # thanks to Jamie Knight for this thing.


class _Variable(object):
    """ Simple data holder.
    """

    def __init__(self, basic, variables):
        self._basic = basic
        self._variables = variables

    @property
    def variables(self):
        """ Values which are the variable points
        """
        return self._variables

    @property
    def basic(self):
        """ The basic place
        """
        return self._basic


class sPyNNakerCFGParameterSwitcher(object):
    """ Explorer of configuration switches
    """

    def __init__(self, machine_name, bmp_names, version, spalloc_server,
                 spalloc_user, user_test_script=None):

        self._static_cfg_params = dict()
        self._machine_cfg_params = dict()
        self._variable_cfg_params = dict()

        self._create_parameters(
            machine_name, bmp_names, version, spalloc_server, spalloc_user)

        self._tests = list()
        self._generate_test_script_file_paths(user_test_script)

        cfg_combinations = self._generate_cfg_combinations()

        self._execute_tests(cfg_combinations)

    def _execute_tests(self, cfg_combinations):
        """ Execute all tests with all combinations

        :param cfg_combinations: the combination of cfg parameters
        :return:
        """
        test_location = os.path.dirname(os.path.realpath(__file__))
        test_location = os.path.join(test_location, "test_folder")
        failed_test_cfg_folder = os.path.join(test_location, "failed_cfgs")
        # make test folder
        if os.path.isdir(test_location):
            shutil.rmtree(test_location)
        os.mkdir(test_location)
        if os.path.isdir(failed_test_cfg_folder):
            shutil.rmtree(failed_test_cfg_folder)
        os.mkdir(failed_test_cfg_folder)

        for test_script_file_path in self._tests:
            self._execute_test(
                test_script_file_path, test_location, cfg_combinations,
                failed_test_cfg_folder)

    def _execute_test(self, test_script_file_path, test_location, combinations,
                      failed_test_cfg_folder):
        """ Goes through all the cfg combinations and tests a script with them

        :param test_script_file_path: the file_path to the test
        :param test_location: the location to test stuff
        :param combinations: the combinations of cfg parameters
        :param failed_test_cfg_folder: the folder to put failed tests
        :return:None
        """

        # move test into test folder where we add the some extra
        # lines to remove issues with matplotlib and codings
        test_script_location = self._move_test_script_to_test_folder(
            test_location, test_script_file_path)

        # iterate through combinations
        failed_test_counter = 1
        for combination in combinations:

            # write a cfg file
            cfg_file_path = os.path.join(test_location, "spynnaker.cfg")
            out = open(cfg_file_path, "w")
            for key, values in combination.iteritems():
                out.write("[{}]\n".format(key))
                for value_key, value_value in values.iteritems():
                    out.write("{} = {}\n".format(value_key, value_value))
            out.flush()
            out.close()

            # try running test
            result = subprocess.call(['python', test_script_location])

            # verify results
            if result != 0:
                # make failed test folder
                failed_folder = \
                    os.path.join(failed_test_cfg_folder,
                                 os.path.basename(test_script_file_path))
                failed_folder += str(failed_test_counter)
                failed_test_counter += 1
                os.mkdir(failed_folder)
                # copy offending script and cfg file to failed test folder
                shutil.copyfile(
                    test_script_location,
                    os.path.join(failed_folder,
                                 os.path.basename(test_script_location)))
                shutil.copyfile(
                    cfg_file_path,
                    os.path.join(failed_folder, "spynnaker.cfg"))

                print "test {} failed. test and cfg file are located in {}"\
                    .format(os.path.basename(test_script_file_path),
                            failed_folder)

    @staticmethod
    def _move_test_script_to_test_folder(
            test_location, original_test_script_file_path):
        """ Move the script to be tested into the test folder.

        :param test_location: the location where the script goes to
        :param original_test_script_file_path: the test script
        :return: the new test script file path
        """
        test_script_file_path = os.path.join(
            test_location, os.path.basename(original_test_script_file_path))

        out = open(test_script_file_path, "w")
        in_file = open(original_test_script_file_path, "r")

        out.write(
            "# coding: utf-8\n"
            "import matplotlib\n"
            "matplotlib.use('Agg')\n")
        temp = in_file.read()
        in_file.close()

        out.write(temp)
        out.flush()
        out.close()
        return test_script_file_path

    def _generate_test_script_file_paths(self, user_test_script):
        """ Locates all scripts for the testing purposes.

        :param user_test_script: the list of user test scripts.
        :return: list of all test scripts.
        """
        if user_test_script is not None:
            self._tests.extend(user_test_script)
        else:
            # locate where i am. as the integration tests are next to me
            location = os.path.dirname(os.path.realpath(__file__))
            for dir_path, _, file_names in os.walk(location):
                for name in file_names:
                    if (name.endswith('.py') and
                            name != "spynnaker_full_tester.py" and
                            name != "__init__.py" and
                            name != "vector_topographic_activity_plot.py" and
                            name != "retina_lib.py" and
                            name != "fake_if_curr.py"):
                        self._tests.append(os.path.join(dir_path, name))

    def _create_parameters(
            self, machine_name, bmp_names, version, spalloc_server,
            spalloc_user):
        """ Creates the parameters and identities which ones are variable,\
            machine based, and static.

        :param machine_name:
            The ip address or domain name for the SpiNNaker machine to
            use for basic runs.
        :param bmp_names:
            The ip address or domain name for the SpiNNaker machines
            BMP connection.
        :param version: The version of the SpiNNaker Machine.
        :param spalloc_server:
            The spalloc server address to be used for finding a SpiNNaker
            machine.
        :param spalloc_user:
            The spalloc user is the identifier that the spalloc server will
            recognise. A email address is a valid identifier.
        :return: None
        """

        # static machine
        self._static_cfg_params["Machine"] = dict()
        self._static_cfg_params["Machine"]["spalloc_port"] = \
            config.get("Machine", "spalloc_port")
        self._static_cfg_params["Machine"]["machine_spec_file"] = None
        self._static_cfg_params["Machine"]["clear_routing_tables"] = \
            config.get("Machine", "clear_routing_tables")
        self._static_cfg_params["Machine"]["clear_tags"] = \
            config.get("Machine", "clear_tags")
        self._static_cfg_params["Machine"][
            "post_simulation_overrun_before_error"] = \
            config.get("Machine", "post_simulation_overrun_before_error")

        # static logging
        self._static_cfg_params["Logging"] = dict()
        self._static_cfg_params["Logging"]["instantiate"] = \
            config.get("Logging", "instantiate")
        self._static_cfg_params["Logging"]["default"] = \
            config.get("Logging", "default")
        self._static_cfg_params["Logging"]["debug"] = \
            config.get("Logging", "debug")
        self._static_cfg_params["Logging"]["info"] = \
            config.get("Logging", "info")
        self._static_cfg_params["Logging"]["warning"] = \
            config.get("Logging", "warning")
        self._static_cfg_params["Logging"]["error"] = \
            config.get("Logging", "error")
        self._static_cfg_params["Logging"]["critical"] = \
            config.get("Logging", "critical")

        # static recording
        self._static_cfg_params["Recording"] = dict()
        self._static_cfg_params["Recording"]["live_spike_port"] = \
            config.get("Recording", "live_spike_port")
        self._static_cfg_params["Recording"]["live_spike_host"] = \
            config.get("Recording", "live_spike_host")

        # static buffers
        self._static_cfg_params["Buffers"] = dict()
        self._static_cfg_params["Buffers"]["receive_buffer_port"] = \
            config.get("Buffers", "receive_buffer_port")
        self._static_cfg_params["Buffers"]["receive_buffer_host"] = \
            config.get("Buffers", "receive_buffer_host")
        self._static_cfg_params["Buffers"]["buffer_size_before_receive"] = \
            config.get("Buffers", "buffer_size_before_receive")
        self._static_cfg_params["Buffers"]["time_between_requests"] = \
            config.get("Buffers", "time_between_requests")
        self._static_cfg_params["Buffers"]["spike_buffer_size"] = \
            config.get("Buffers", "spike_buffer_size")
        self._static_cfg_params["Buffers"]["v_buffer_size"] = \
            config.get("Buffers", "v_buffer_size")
        self._static_cfg_params["Buffers"]["gsyn_buffer_size"] = \
            config.get("Buffers", "gsyn_buffer_size")
        self._static_cfg_params["Buffers"]["minimum_buffer_sdram"] = \
            config.get("Buffers", "minimum_buffer_sdram")

        # static mode
        self._static_cfg_params["Mode"] = dict()
        self._static_cfg_params["Mode"]["mode"] = \
            config.get("Mode", "mode")
        self._static_cfg_params["Mode"]["verify_writes"] = \
            config.get("Mode", "verify_writes")

        # static database
        self._static_cfg_params["Database"] = dict()
        self._static_cfg_params["Database"]["create_database"] = \
            config.get("Database", "create_database")
        self._static_cfg_params["Database"]["wait_on_confirmation"] = \
            config.get("Database", "wait_on_confirmation")
        self._static_cfg_params["Database"]["send_start_notification"] = \
            config.get("Database", "send_start_notification")
        self._static_cfg_params["Database"][
            "create_routing_info_to_neuron_id_mapping"] = \
            config.get("Database", "create_routing_info_to_neuron_id_mapping")
        self._static_cfg_params["Database"]["listen_port"] = \
            config.get("Database", "listen_port")
        self._static_cfg_params["Database"]["notify_port"] = \
            config.get("Database", "notify_port")
        self._static_cfg_params["Database"]["notify_hostname"] = \
            config.get("Database", "notify_hostname")

        # static mapping
        self._static_cfg_params["Mapping"] = dict()
        self._static_cfg_params["Mapping"]["extra_xmls_paths"] = None

        # static mode
        self._static_cfg_params["Mode"] = dict()
        self._static_cfg_params["Mode"][
            "violate_1ms_wall_clock_restriction"] = False

        # static master pop
        self._static_cfg_params["MasterPopTable"] = dict()
        self._static_cfg_params["MasterPopTable"]["generator"] = "BinarySearch"

        # static spec execute
        self._static_cfg_params["SpecExecution"] = dict()
        self._static_cfg_params["SpecExecution"]["specExecOnHost"] = True

        # static mapping
        self._static_cfg_params["Mapping"] = dict()
        self._static_cfg_params["Mapping"][
            "partitioned_to_machine_algorithms"] = \
            "GraphEdgeFilter,RadialPlacer,RigRoute,BasicTagAllocator," \
            "FrontEndCommonEdgeToNKeysMapper,MallocBasedRoutingInfo" \
            "Allocator,BasicRoutingTableGenerator,MundyRouterCompressor"\
            ",SpynnakerDatabaseWriter"

        self._static_cfg_params["Mapping"][
            "partitionable_to_partitioned_algorithms"] = \
            "PartitionAndPlacePartitioner"

        # static reinjection
        self._static_cfg_params["Machine"]["enable_reinjection"] = False

        # static app stop
        self._static_cfg_params["Machine"]["use_app_stop"] = False

        # static sdram cap
        self._static_cfg_params["Machine"]["max_sdram_allowed_per_chip"] = None

        # static machine time step and time scale factor
        self._static_cfg_params["Machine"]["machineTimeStep"] = None
        self._static_cfg_params["Machine"]["timeScaleFactor"] = None

        # static auto detect BMP
        self._static_cfg_params["Machine"]["auto_detect_bmp"] = False

        # dynamic machine
        self._variable_cfg_params = list()

        data = dict()
        data["Machine"] = dict()
        data["Machine"]["machineName"] =\
            _Variable(machine_name,
                      [None, None, None, None, None, None])
        data["Machine"]["bmp_names"] = \
            _Variable(bmp_names,
                      [None, None, None, None, None, None])
        data["Machine"]["version"] = \
            _Variable(version,
                      [None, None, 3, 2, 4, 5])
        data["Machine"]["spalloc_server"] = \
            _Variable(None,
                      [spalloc_server, None, None, None, None, None])
        data["Machine"]["spalloc_user"] = \
            _Variable(None,
                      [spalloc_user, None, None, None, None, None])
        data["Machine"]["virtual_board"] = \
            _Variable(False,
                      [None, True, True, True, True, True])
        data["Machine"]["requires_wrap_arounds"] = \
            _Variable(None,
                      [None, True, True, True, True, True])
        data["Machine"]["width"] = \
            _Variable(None,
                      [None, 8, None, None, None, None])
        data["Machine"]["height"] = \
            _Variable(None,
                      [None, 8, None, None, None, None])
        self._machine_cfg_params = dict(data)

        data = dict()
        data["Machine"] = dict()
        data["Machine"]["turn_off_machine"] = _Variable(False, [True])
        self._variable_cfg_params.append(data)

        data = dict()
        data["Machine"] = dict()
        data["Machine"]["reset_machine_on_startup"] = _Variable(False, [True])
        self._variable_cfg_params.append(data)

        data = dict()
        data["Buffers"] = dict()
        data["Buffers"]["enable_buffered_recording"] = \
            _Variable(False, [True])
        self._variable_cfg_params.append(data)

        data = dict()
        data["Buffers"] = dict()
        data["Buffers"]["use_auto_pause_and_resume"] = \
            _Variable(True, [False])
        self._variable_cfg_params.append(data)

    def _generate_cfg_combinations(self):
        """ Generate the cfg combinations

        :return: return the set of cfg parameter combinations
        """
        combination_base = dict()

        for field in self._static_cfg_params:
            if field not in combination_base:
                combination_base[field] = dict()
            for element, value in self._static_cfg_params[field].items():
                combination_base[field][element] = value

        # handle machine variable stuff
        combinations = list()
        self._sort_out_machine_combinations(
            combination_base, combinations)

        self._add_basic_machine(combination_base)

        # handle other variables
        position = 0
        self._iterate_variable_params(
            combination_base, position, combinations,
            self._variable_cfg_params)
        return combinations

    def _add_basic_machine(self, combination_base):
        """ Add the machine's basic parameter set

        :param combination_base: the combination to add these parameters to
        :return: None
        """
        for variable in self._machine_cfg_params:
            fields = self._machine_cfg_params[variable].keys()
            for field in fields:
                combination_base[variable][field] = \
                    self._machine_cfg_params[variable][field].basic

    def _sort_out_machine_combinations(self, combination_base, combinations):
        """ Sort out the machine exploration so that it doesn't overload the\
            test suite

        :param combination_base: the combination base to start with
        :param combinations: the set of complete combinations
        :return:
        """
        combination = copy.deepcopy(combination_base)
        for variable in self._variable_cfg_params:
            fields = variable.keys()
            for field in fields:
                if field not in combination:
                    combination[field] = dict()

            for field in fields:
                items = variable[field].keys()
                for item in items:
                    combination[field][item] = variable[field][item].basic

        self._iterate_variable_params(
            combination, 0, combinations, [self._machine_cfg_params])

    def _iterate_variable_params(
            self, combination_base, position, combinations, variables):
        """ Recursive method to iterate though the parameters for some\
            variables

        :param combination_base: the current combination to start adding to
        :param position: the position in the variables to iterate through
        :param combinations: the cfg combinations
        :return: None
        """
        if position == len(variables):
            combinations.append(copy.deepcopy(combination_base))
        else:
            combination = copy.deepcopy(combination_base)
            variable = variables[position]
            fields = variable.keys()
            for field in fields:
                if field not in combination:
                    combination[field] = dict()

            for field in fields:

                items = variable[field].keys()
                for item in items:
                    combination[field][item] = variable[field][item].basic

                # add basic to combinations
                next_pos = position + 1
                self._iterate_variable_params(
                    combination, next_pos, combinations, variables)

                # add variables
                combination = copy.deepcopy(combination_base)
                size = len(variable[field][items[0]].variables)
                for variable_position in range(0, size):
                    for item in items:
                        combination[field][item] = \
                            variable[field][item].variables[variable_position]
                    # add basic to combinations
                    next_pos = position + 1
                    self._iterate_variable_params(
                        combination, next_pos, combinations, variables)


def main():
    """ Entrance when running directly.
    """

    # build parser
    parser = argparse.ArgumentParser(
        description=(
            'Executes either a fixed set of tests or all integration tests.'))
    parser.add_argument(
        'machine_name', type=str,
        help="The ip address or domain name for the SpiNNaker machine to "
             "use for basic runs.")
    parser.add_argument(
        'bmp_names', type=str,
        help="The ip address or domain name for the SpiNNaker machines "
             "BMP connection.")
    parser.add_argument(
        'version', type=int, choices=[2, 3, 4, 5],
        help="The version of the SpiNNaker Machine.")
    parser.add_argument(
        'spalloc_server', type=str,
        help="The spalloc server address to be used for finding a "
             "SpiNNaker machine.")
    parser.add_argument(
        'spalloc_user', type=str,
        help="The spalloc user is the identifier that the spalloc server will "
             "recognise. A email address is a valid identifier.")
    parser.add_argument(
        '--tests', default=None, type=str, nargs='+',
        help="The list of test file paths which the users wants to use. "
             "If none are provided, all the integration tests will be ran.")

    # parse arguments
    args = parser.parse_args()

    # map arguments for ease
    machine_name = args.machine_name
    bmp_names = args.bmp_names
    version = args.version
    spalloc_server = args.spalloc_server
    spalloc_user = args.spalloc_user
    tests = args.tests

    # inform user of args, for verification
    print "Will be running a test suite with parameters:"
    print "     machine_name = {}".format(machine_name)
    print "     bmp_names = {}".format(bmp_names)
    print "     version = {}".format(version)
    print "     spalloc_server = {}".format(spalloc_server)
    print "     spalloc_user = {}".format(spalloc_user)
    print "     tests = "
    for test in tests:
        print "         {}".format(test)

    # run tester
    sPyNNakerCFGParameterSwitcher(
        machine_name, bmp_names, version, spalloc_server, spalloc_user, tests)

if __name__ == "__main__":
    main()
