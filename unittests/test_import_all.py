import unittest
import os
import spinn_utilities.package_loader as package_loader


class ImportAllModule(unittest.TestCase):

    def test_import_all(self):
        print os.environ.get('CONTINUOUS_INTEGRATION', None)
        print os.environ.get('TRAVIS', None)
        print os.environ.get('CI', None)
        if os.environ.get('CONTINUOUS_INTEGRATION', None) == 'True':
            package_loader.load_module("spynnaker", remove_pyc_files=False)
        else:
            package_loader.load_module("spynnaker", remove_pyc_files=True)
