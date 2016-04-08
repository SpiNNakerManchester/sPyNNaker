from integration_tests.spynnaker_full_tester import\
    SpYNNakerCFGParameterSwitcher


def main():
    """
    run test suite for my machine
    :return:
    """
    machine_name = "spinn-1"
    bmp_names = "spinn-1c"
    version = 5
    spalloc_server = "cspc276.cs.man.ac.uk"
    spalloc_user = "alan.barry.stokes@gmail.com"

    tests = list()
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/"
        "PyNNExamples/examples/va_benchmark.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/"
        "PyNNExamples/examples/stdp_example.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/"
        "PyNNExamples/examples/stdp_curve.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/"
        "PyNNExamples/examples/stdp_example.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/sPyNNaker"
        "/intergration_tests/auto_pause_and_resume_tests/synfire_1_run_no"
        "_extraction_if_curr_exp_low_sdram.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/sPyNNaker"
        "/intergration_tests/multi_call_examples/spike_io_multi_run.py")
    tests.append(
        "/home/S06/stokesa6/spinniker/alpha_package_103_git/sPyNNaker"
        "/intergration_tests/multi_call_examples/"
        "synfire_3_run_1_exit_no_extraction_if_curr_exp.py")

    SpYNNakerCFGParameterSwitcher(
        machine_name, bmp_names, version, spalloc_server, spalloc_user, tests)

if __name__ == "__main__":
    main()

