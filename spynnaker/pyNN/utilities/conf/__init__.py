"""
Import Config Files
-------------------
We look for config files in a variety of locations starting with the package
directory, followed by the user's home directory and ending with the current
working directory.

All config is made accessible through the global object `config`.
"""
import ConfigParser
import logging
import os
import shutil
import string
import sys

import spynnaker
from spinn_front_end_common.utilities import exceptions
from spynnaker.pyNN.utilities.conf import log


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
spynnaker_others = (spynnaker_user, "spynnaker.cfg")
located_spynnaker = list()

found_spynnakers = False
for possible_spynnaker_file in spynnaker_others:
    if os.path.isfile(possible_spynnaker_file):
        found_spynnakers = True
        located_spynnaker.append(os.path.abspath(possible_spynnaker_file))


with open(default) as f:
    config.readfp(f)
if found_spynnakers:
    read = config.read(spynnaker_others)
else:
    # Create a default spynnaker.cfg in the user home directory and get them
    # to update it.
    _install_cfg()

read.append(default)

machine_spec_file_path = config.get("Machine", "machine_spec_file")
if machine_spec_file_path != "None":
    config.read(machine_spec_file_path)
    read.append(machine_spec_file_path)


# creates a directory if needed, or deletes it and rebuilds it
def create_directory(directory):
    """

    :param directory:
    :return:
    """
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
