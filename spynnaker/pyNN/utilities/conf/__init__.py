"""
Import Config Files
-------------------
We look for config files in a variety of locations starting with the package
directory, followed by the user's home directory and ending with the current
working directory.

All config is made accessible through the global object `config`.
"""
import spynnaker
from spinn_utilities.conf_loader import ConfigurationLoader

_loader = ConfigurationLoader(spynnaker, "spynnaker.cfg")

# Create a config, read global defaults and then read in additional files
config = _loader.load_config()

__all__ = ['config']
