# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.version import StrictVersion  # pylint: disable=all
from six import raise_from
from pyNN import __version__ as _pynn_version
from neo import __version__ as _neo_version


_SUPPORTED_MSG = (
    "pyNN version {} and neo version {} are not supported together.\n"
    "Tested combinations are:\n"
    "\tpyNN 0.8.3 and neo 0.4.0, or\n"
    "\tpyNN 0.8.3 and neo 0.4.1, or\n"
    "\tpyNN 0.9.1 and neo 0.5.2, or\n"
    "\tpyNN 0.9.2 and neo 0.6.1")


def detect_supported_configuration(pynn_version, neo_version):
    """ Check if the version configuration of PyNN and Neo is one we support.

    .. note::
        We strongly encourage the use of PyNN 0.9 and Neo 0.6.

    :return: True if we're using old PyNN 0.8 syntax
    :raises ImportError: If a truly unsupported system is present or if we\
        cannot parse the version numbers (shouldn't happen)
    """
    try:
        pynn = StrictVersion(pynn_version)
    except Exception as e:  # pylint: disable=broad-except
        raise_from(ImportError("couldn't parse pyNN version number"), e)
    try:
        neo = StrictVersion(neo_version)
    except Exception as e:  # pylint: disable=broad-except
        raise_from(ImportError("couldn't parse neo version number"), e)

    if pynn >= "0.9":
        if neo < "0.5":
            raise ImportError(_SUPPORTED_MSG.format(pynn, neo))
        return False
    elif pynn >= "0.8":
        if neo < "0.3" or neo >= "0.5":
            raise ImportError(_SUPPORTED_MSG.format(pynn, neo))
        print("WARNING: PyNN 0.8 is deprecated at the request of the PyNN "
              "team.")
        print("Please upgrade your PyNN and Neo installations to at least "
              "PyNN 0.9.2 and Neo 0.5.2")
        print("If you specifically need PyNN 0.8 please contact us *URGENTLY* "
              "otherwise PyNN 0.8 will be removed with the next sub-release "
              "(i.e., before PyNN 0.7 support is removed).")
        return True
    else:
        # Really old version of PyNN?! How...
        raise ImportError(_SUPPORTED_MSG.format(pynn, neo))


print("Detected PyNN version {} and Neo version {}".format(
    _pynn_version, _neo_version))
pynn8_syntax = detect_supported_configuration(_pynn_version, _neo_version)
