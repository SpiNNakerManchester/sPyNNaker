"""
Import Config Files
-------------------
We look for config files in a variety of locations starting with the package
directory, followed by the user's home directory and ending with the current
working directory.

All config is made accessible through the global object `config`.
"""
import ConfigParser
import inspect
import logging
import os
import re
import shutil
import string
import spynnaker
from . import log

# Create a config, read global defaults and then read in additional files
config = ConfigParser.RawConfigParser()
defaults = os.path.join(os.path.dirname(spynnaker.__file__), "pacman.cfg")
with open(defaults) as f:
    config.readfp(f)
read = config.read(["pacman.cfg", os.path.expanduser("~/.pacman.cfg")])
read.append(defaults)


# Get lists of appropriate routers, placers and partitioners
def get_valid_components(module, terminator):
    terminator = re.compile(terminator + '$')
    return dict(map(lambda (name, router): (terminator.sub('', name), router),
                inspect.getmembers(module, inspect.isclass)))


# creates a directory if needed, or deletes it and rebuilds it
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)


# Create the root logger with the given level
# Create filters based on logging levels
try:
    if config.getboolean("Logging", "instantiate"):
        logging.basicConfig(level=0)

    for handler in logging.root.handlers:
        handler.addFilter(log.ConfiguredFilter(config))
        handler.setFormatter(log.ConfiguredFormatter(config))
except ConfigParser.NoSectionError:
    pass
except ConfigParser.NoOptionError:
    pass

# Log which config files we read
logger = logging.getLogger(__name__)
logger.info("Read config files: %s" % string.join(read, ", "))
