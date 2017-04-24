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

    def assert_logs_error(self, log_records, sub_message):
        for record in log_records:
            if record.levelname == 'ERROR':
                if sub_message in record.msg:
                    return
        msg = "\"{}\" not found in any ERROR logs".format(sub_message)
        raise self.failureException(msg)
