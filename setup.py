import os
from setuptools import setup
exec(open("spynnaker/pyNN/_version.py").read())

if os.environ.get('READTHEDOCS', None) == 'True':
    # scipy must be added in config.py as a mock
    install_requires = ['SpiNNFrontEndCommon >= 3.0.0, < 4.0.0',
                        'pyNN >= 0.7, < 0.8', 'numpy', 'lxml', 'six']
else:
    install_requires = ['SpiNNFrontEndCommon >= 3.0.0, < 4.0.0',
                        'pyNN >= 0.7, < 0.8', 'numpy', 'scipy', 'lxml', 'six']

setup(
    name="sPyNNaker",
    version=__version__,
    description="Spinnaker implementation of PyNN",
    url="https://github.com/SpiNNakerManchester/SpyNNaker",
    packages=['spynnaker',
              'spynnaker.pyNN',
              'spynnaker.pyNN.model_binaries',
              'spynnaker.pyNN.models',
              'spynnaker.pyNN.models.abstract_models',
              'spynnaker.pyNN.models.common',
              'spynnaker.pyNN.models.neural_projections',
              'spynnaker.pyNN.models.neural_projections.connectors',
              'spynnaker.pyNN.models.neural_properties',
              'spynnaker.pyNN.models.neuron',
              'spynnaker.pyNN.models.neuron.additional_inputs',
              'spynnaker.pyNN.models.neuron.builds',
              'spynnaker.pyNN.models.neuron.input_types',
              'spynnaker.pyNN.models.neuron.master_pop_table_generators',
              'spynnaker.pyNN.models.neuron.neuron_models',
              'spynnaker.pyNN.models.neuron.plasticity',
              'spynnaker.pyNN.models.neuron.plasticity.stdp',
              'spynnaker.pyNN.models.neuron.plasticity.stdp.common',
              'spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure',
              'spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence',
              'spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence',
              'spynnaker.pyNN.models.neuron.synapse_dynamics',
              'spynnaker.pyNN.models.neuron.synapse_io',
              'spynnaker.pyNN.models.neuron.synapse_types',
              'spynnaker.pyNN.models.neuron.threshold_types',
              'spynnaker.pyNN.models.spike_source',
              'spynnaker.pyNN.models.utility_models',
              'spynnaker.pyNN.overridden_pacman_functions',
              'spynnaker.pyNN.utilities',
              'spynnaker.pyNN.utilities.conf',
              'spynnaker.pyNN.utilities.random_stats',],
    package_data={'spynnaker.pyNN.model_binaries': ['*.aplx'],
                  'spynnaker': ['spynnaker.cfg'],
                  'spynnaker.pyNN.utilities.conf': ['spynnaker.cfg.template'],
                  'spynnaker.pyNN.overridden_pacman_functions': ['*.xml']},
    install_requires=install_requires
)
