[![Build Status](https://travis-ci.org/SpiNNakerManchester/sPyNNaker.svg?branch=master)](https://travis-ci.org/SpiNNakerManchester/sPyNNaker)
[![Documentation Status](https://readthedocs.org/projects/spynnaker/badge/?version=master)](https://spynnaker.readthedocs.io/en/master/?badge=master)
[![Coverage Status](https://coveralls.io/repos/github/SpiNNakerManchester/sPyNNaker/badge.svg?branch=master)](https://coveralls.io/github/SpiNNakerManchester/sPyNNaker?branch=master)

sPyNNaker - PyNN Simulations on SpiNNaker Hardware
==================================================
This package provides common code for PyNN implementations for SpiNNaker.

We have [user installation instructions](http://spinnakermanchester.github.io/)
which describe in detail more about what is going on. Note that this package is
not intended to be used directly; the `sPyNNaker7` and `sPyNNaker8` packages
contain the user-facing APIs, and you should use the one that corresponds to
the version of PyNN you wish to work with.

Developer Installation
----------------------
If you want to be able to edit the source code, but still have it referenced
from other Python modules, you can set the install to be a
[developer install](http://spinnakermanchester.github.io/development/devenv.html)
which describes the process of installing not only the `sPyNNaker7` and `sPyNNaker8`
packages for accessing the user-facing APIs, but also the other modules which these
depend upon for a complete editable install.


Documentation
-------------
[sPyNNaker python documentation](http://spynnaker.readthedocs.io)
[Combined PyNN7 python documentation](http://spinnaker7manchester.readthedocs.io)
[Combined PyNN8 python documentation](http://spinnaker8manchester.readthedocs.io)
