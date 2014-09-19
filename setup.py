try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="sPyNNaker",
    version="0.1-SNAPSHOT",
    description="Spinnaker implementation of PyNN",
    url="https://github.com/SpiNNakerManchester/SpyNNaker",
    packages=['spynnaker',
              'spynnaker.pyNN',
              'spynnaker.pyNN.data_storage',
              'spynnaker.pyNN.models',
              'spynnaker.pyNN.models.abstract_models',
              'spynnaker.pyNN.models.neural_models',
              'spynnaker.pyNN.models.neural_projections',
              'spynnaker.pyNN.models.neural_projections.connectors',
              'spynnaker.pyNN.models.neural_properties',
              'spynnaker.pyNN.models.neural_properties.synapse_dynamics',
              'spynnaker.pyNN.models.spike_source',
              'spynnaker.pyNN.models.utility_models',
              'spynnaker.pyNN.overridden_pacman_functions',
              'spynnaker.pyNN.utilities',
              'spynnaker.pyNN.utilities.conf',
              'spynnaker.pyNN.visualiser_package',
              'spynnaker.pyNN.visualiser_package.visualiser_pages'],
    install_requires=['SpiNNMachine', 'SpiNNMan', 'PACMAN',
            'DataSpecification', 'Visualiser', 'pyNN']
)
