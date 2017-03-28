try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install

import os

__version__ = "3.0.0"


class CustomInstall(install):
    def initialize_options(self):
        install.initialize_options(self)
        self._spinnaker_dir = None
        self._spinnaker_init = None

        import pyNN
        pynn_path = os.path.dirname(pyNN.__file__)
        self._spinnaker_dir = os.path.join(pynn_path, "spiNNaker")
        self._spinnaker_init = os.path.join(self._spinnaker_dir, "__init__.py")

    def run(self):
        if not os.path.exists(self._spinnaker_dir):
            os.mkdir(self._spinnaker_dir)
        if not os.path.exists(self._spinnaker_init):
            spinn_file = open(self._spinnaker_init, "w")
            spinn_file.write("from spynnaker.pyNN import *\n")
            spinn_file.write("__version__ = \"{}\"\n".format(__version__))
            spinn_file.close()
            print "Created", self._spinnaker_init
        install.run(self)

    def get_outputs(self):
        outputs = install.get_outputs(self)
        outputs.append(self._spinnaker_init)
        return outputs


setup(
    name="pyNN-spiNNaker",
    version=__version__,
    description="Tools for the SpiNNaker platform.",
    url="https://github.com/SpiNNakerManchester/SpyNNaker",
    packages=[],
    install_requires=['pyNN >= 0.7, < 0.8',
                      'sPyNNaker >= 3.0.0, < 4.0.0'],
    cmdclass={'install': CustomInstall})
