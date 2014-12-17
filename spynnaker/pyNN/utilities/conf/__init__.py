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
import sys
import spynnaker
from spynnaker.pyNN import exceptions
from . import log


def _install_cfg():
    template_cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                "spynnaker.cfg.template")
    home_cfg = os.path.expanduser("~/.spynnaker.cfg")
    shutil.copyfile(template_cfg, home_cfg)
    print "************************************"
    print("{} has been created.  Please edit this file and change \"None\""
          " after \"machineName\" to the hostname or IP address of your"
          " SpiNNaker board, and change \"None\" after \"version\" to the"
          " version of SpiNNaker hardware you are running on:".format(
                   home_cfg))
    print "[Machine]"
    print "machineName = None"
    print "version = None"
    print "************************************"
    sys.exit(0)

# Create a config, read global defaults and then read in additional files
config = ConfigParser.RawConfigParser()
default = os.path.join(os.path.dirname(spynnaker.__file__), "spynnaker.cfg")
spynnaker_user = os.path.expanduser("~/.spynnaker.cfg")
spynnaker_others = ("spynnaker.cfg", spynnaker_user)

legacy_pacmans = (os.path.expanduser("~/.pacman.cfg"), "pacman.cfg")

found_spynnakers = False
for possible_spynnaker_file in spynnaker_others:
    if os.path.isfile(possible_spynnaker_file):
        found_spynnakers = True

found_pacmans = False
for possible_pacman_file in legacy_pacmans:
    if os.path.isfile(possible_pacman_file):
        if found_spynnakers:
            raise exceptions.ConfigurationException(
                "The configuration tools discovered a spynnaker.cfg in path \n"
                "{}\n as well as a non-default spynnaker.cfg. Spynnaker does"
                " not support integration of pacman.cfg and spynnaker.cfg."
                " Please remove or merge these files. Recommendation is to"
                " rename the merged file to spynnaker.cfg".format(
                    possible_pacman_file))
        else:
            found_pacmans = True

with open(default) as f:
    config.readfp(f)
if found_spynnakers:
    read = config.read(spynnaker_others)
elif found_pacmans:
    read = config.read(legacy_pacmans)
else:

    # Create a default pacman.cfg in the user home directory and get them
    # to update it.
    _install_cfg()

read.append(default)


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
