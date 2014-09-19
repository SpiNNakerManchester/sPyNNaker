try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="pyNN",
    version="-spiNNaker-0.1-SNAPSHOT",
    description="Tools for the SpiNNaker platform.",
    url="https://github.com/SpiNNakerManchester/SpyNNaker",
    package_dir={'': 'pyNN-spiNNaker-src'},
    packages=['pyNN.spiNNaker'],
    zip_safe=False,
    install_requires=['pyNN', 'sPyNNaker']
)
