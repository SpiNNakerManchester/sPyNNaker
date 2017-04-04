import os

import spynnaker.pyNN.utilities.utility_calls as utility_calls


def check_gsyn(gsyn1, gsyn2):
    if len(gsyn1) != len(gsyn2):
        raise Exception("Length of gsyn does not match expected {} but "
                        "found {}".format(len(gsyn1), len(gsyn2)))
    for i in range(len(gsyn1)):
        for j in range(3):
            if round(gsyn1[i][j], 1) != round(gsyn2[i][j], 1):
                raise Exception("Mismatch between gsyn found at position {}{}"
                                "expected {} but found {}".
                                format(i, j, gsyn1[i][j], gsyn2[i][j]))


def check_path_gysn(path, n_neurons, runtime, gsyn):
    gsyn2 = utility_calls.read_in_data_from_file(path, 0, n_neurons,
                                                 0, runtime)
    check_gsyn(gsyn, gsyn2)


def check_sister_gysn(sister, n_neurons, runtime, gsyn):
    dir = os.path.dirname(os.path.abspath(sister))
    path = os.path.join(dir, "gsyn.data")
    check_path_gysn(path, n_neurons, runtime, gsyn)
