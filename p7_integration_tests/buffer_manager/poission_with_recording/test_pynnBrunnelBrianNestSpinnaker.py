import unittest

import p7_integration_tests.buffer_manager.poission_with_recording.\
    pynnBrunnelPlot as pblt

from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'


def plot(esp, sim_time, N_E):
    import pylab  # deferred so unittest are not dependent on it
    if esp is not None:
        ts_ext = [x[1] for x in esp]
        ids_ext = [x[0] for x in esp]
        title = 'Raster Plot of the excitatory population in %s' \
                % simulator_Name,
        pblt._make_plot(ts_ext, ts_ext, ids_ext, ids_ext,
                        len(ts_ext) > 0, 5.0, False, title,
                        'Simulation Time (ms)', total_time=sim_time,
                        n_neurons=N_E)

        pylab.show()


class PynnBrunnelBrianNestSpinnaker(BaseTestCase):

    # Raises SpinnmanException: 30 cores have reached an error state
    # CPUState.RUN_TIME_EXCEPTION:
    # See prior_integration_tests/buffer_manager/
    # poission_with_recording/pynnBrunnelBrianNestSpinnaker.py
    @unittest.skip("Skipped buffer_manager/"
                   "poission_with_recording/"
                   "test_pynnBrunnelBrianNestSpinnaker")
    def test_run(self):
        (esp, s, N_E) = script.do_run(Neurons, sim_time, True)


if __name__ == '__main__':
    (esp, s, N_E) = script.do_run(Neurons, sim_time, True)
    plot(esp, sim_time, N_E)
