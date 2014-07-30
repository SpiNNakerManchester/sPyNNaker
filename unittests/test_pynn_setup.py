#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pynn
class PyNNTests(unittest.TestCase):
    """
    Test the Machine class
    """
    def test_initial_setup(self):
        self.assertEqual(pynn.setup(timestep=1, min_delay=1, max_delay=15.0),None)
        # self.assertTrue(pynn.controller != None)
        # self.assertTrue(pynn.appMonitorVertex != None)
        #self.assertTrue(pynn.multi_cast_vertex != None)
        #pynn.run(100)
        # pynn.end()
        # self.assertTrue(pynn.controller == None)
    #
    # def test_setting_up_again(self):
    #     print "\n-----------------Setting up pyNN a second time-----------------\n"
    #     pynn.setup(timestep=1.1, min_delay=1.1, max_delay=10.0)
    #     #pynn.run(100)
    #     #pynn.end()
    #
    # def test_setting_up_again_after_end(self):
    #     print "\n-----Setting up pyNN a third time after trying to run end------\n"
    #     pynn.end()
    #     pynn.setup(timestep=1.1, min_delay=1.1, max_delay=10.0)
    #     #pynn.run(100)
    #     #pynn.end()
    #
    # def test_setting_up_again_after_manually_resetting_values(self):
    #     print "Setting up pyNN a fourth time after manually setting ",\
    #         "Controller, appMonitorVertex and multi_cast_vertex to None"
    #     # pynn.controller = None
    #     # pynn.appMonitorVertex = None
    #     # pynn.multi_cast_vertex = None
    #     pynn.setup(timestep=1.1, min_delay=1.1, max_delay=10.0)
    #     #pynn.run(100)
    #     #pynn.end()



if __name__=="__main__":
    unittest.main()
