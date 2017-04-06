import os
import sys
import unittest

import spynnaker.pyNN.utilities.conf as conf
from spynnaker.pyNN.spinnaker import Spinnaker as Spinnaker


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)
        config = conf.load_config()
        Spinnaker._set_config(config)
