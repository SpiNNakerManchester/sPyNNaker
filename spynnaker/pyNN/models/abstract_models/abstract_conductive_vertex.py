from spynnaker.pyNN.utilities import utility_calls


class AbstractConductiveVertex(object):

    def __init__(self, n_neurons, e_rev_e, e_rev_i):

        self._e_rev_e = utility_calls.convert_param_to_numpy(e_rev_e, n_neurons)
        self._e_rev_i = utility_calls.convert_param_to_numpy(e_rev_i, n_neurons)