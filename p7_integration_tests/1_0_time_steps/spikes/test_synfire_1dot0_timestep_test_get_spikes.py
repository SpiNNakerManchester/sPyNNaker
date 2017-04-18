"""
Synfirechain-like example
"""
import unittest
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

n_neurons = 200
timestep = 1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons / 2
runtime = 500
synfire_run = TestRun()


class TestGetSpikesAt0_1msTimeStep(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def test_get_spikes(self):
        """
        test for get spikes
        """
        synfire_run.do_run(n_neurons, time_step=timestep, max_delay=max_delay,
                           delay=delay, neurons_per_core=neurons_per_core,
                           run_times=[runtime])
        spikes = synfire_run.get_output_pop_spikes()

        pre_recorded_spikes = [[0, 3], [1, 7], [2, 11], [3, 15], [4, 19],
                               [5, 23], [6, 27], [7, 31], [8, 35], [9, 39],
                               [10, 43], [11, 47], [12, 51], [13, 55],
                               [14, 59], [15, 63], [16, 67], [17, 71],
                               [18, 75], [19, 79], [20, 83], [21, 87],
                               [22, 91], [23, 95], [24, 99], [25, 103],
                               [26, 107], [27, 111], [28, 115], [29, 119],
                               [30, 123], [31, 127], [32, 131], [33, 135],
                               [34, 139], [35, 143], [36, 147], [37, 151],
                               [38, 155], [39, 159], [40, 163], [41, 167],
                               [42, 171], [43, 175], [44, 179], [45, 183],
                               [46, 187], [47, 191], [48, 195], [49, 199],
                               [50, 203], [51, 207], [52, 211], [53, 215],
                               [54, 219], [55, 223], [56, 227], [57, 231],
                               [58, 235], [59, 239], [60, 243], [61, 247],
                               [62, 251], [63, 255], [64, 259], [65, 263],
                               [66, 267], [67, 271], [68, 275], [69, 279],
                               [70, 283], [71, 287], [72, 291], [73, 295],
                               [74, 299], [75, 303], [76, 307], [77, 311],
                               [78, 315], [79, 319], [80, 323], [81, 327],
                               [82, 331], [83, 335], [84, 339], [85, 343],
                               [86, 347], [87, 351], [88, 355], [89, 359],
                               [90, 363], [91, 367], [92, 371], [93, 375],
                               [94, 379], [95, 383], [96, 387], [97, 391],
                               [98, 395], [99, 399], [100, 403], [101, 407],
                               [102, 411], [103, 415], [104, 419], [105, 423],
                               [106, 427], [107, 431], [108, 435], [109, 439],
                               [110, 443], [111, 447], [112, 451], [113, 455],
                               [114, 459], [115, 463], [116, 467], [117, 471],
                               [118, 475], [119, 479], [120, 483], [121, 487],
                               [122, 491], [123, 495], [124, 499]]

        for spike_element, read_element in zip(spikes, pre_recorded_spikes):
            self.assertEqual(spike_element[0], read_element[0])
            self.assertAlmostEqual(spike_element[1], read_element[1],
                                   delta=0.4)


if __name__ == '__main__':
    unittest.main()
