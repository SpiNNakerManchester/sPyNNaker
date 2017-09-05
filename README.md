[![Build Status](https://travis-ci.org/SpiNNakerManchester/sPyNNaker.svg?branch=master)](https://travis-ci.org/SpiNNakerManchester/sPyNNaker)

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
from other Python modules, you can set the install to be a developer install.
In this case, download the source code, and extract it locally, or else clone
the git repository:

    git clone http://github.com/SpiNNakerManchester/sPyNNaker.git

To install as a development version which all users will then be able to use,
run the following where the code has been extracted:

    sudo python setup.py develop

To install as a development version for only yourself, run:

    python setup.py develop --user

If you also want pyNN.spiNNaker support, please install this as described above.

Documentation
-------------
[sPyNNaker python documentation](http://spynnaker.readthedocs.io)  
[Combined PyNN7 python documentation](http://spinnaker7manchester.readthedocs.io)  
[Combined PyNN8 python documentation](http://spinnaker8manchester.readthedocs.io)
