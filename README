This package provides a PyNN implementation for SpiNNaker.

Requirements
============
In addition to a standard Python installation, this package depends on:
 - six
 - enum34
 - DataSpecification
 - PACMAN
 - SpiNNMan
 - PyNN
 - numpy

You can also optionally install:
 - Visualiser (for live visualisation support)

These dependencies, excluding numpy, can be installed using pip:
    pip install six
    pip install enum34
    pip install DataSpecification
    pip install PACMAN
    pip install SpiNNMan
    pip install PyNN

To install the Visualiser, please see the Visualiser README, as this contains
details of how to install GTK.

Details of the installation of numpy on various operating systems are shown
below.

If you are using virtualenv, please also follow the instructions below to
install numpy.  Further instructions for adding this global package
to your virutalenv are detailed in the "User Installation" and
"Developer Installation" sections below.

Ubuntu Linux
------------
Execute the following to install both gtk and pygtk:
    sudo apt-get install python-numpy

Fedora Linux
------------
Execute the following to install both gtk and pygtk:
    sudo yum install numpy

Windows 7/8 64-bit
------------------
Download and install http://spinnaker.cs.manchester.ac.uk/.../numpy-MKL-1.8.1.win-amd64-py2.7.exe

Windows 7/8 32-bit
------------------
Download and install http://spinnaker.cs.manchester.ac.uk/.../numpy-MKL-1.8.1.win32-py2.7.exe


User Installation
=================
If you want to install for all users, run:
    sudo pip install sPyNNaker

If you want to install only for yourself, run:
    pip install sPyNNaker --user

To install in a virtualenv, it is easier if numpy is installed outside of the
virtualenv first.  This is done by creating a link to the system numpy in the
virtual env (with the virtualenv activated):
    32-bit Fedora Linux:
        ln -s /usr/lib/python2.7/site-packages/numpy $VIRTUAL_ENV/lib/python2.7/site-packages/numpy
        ln -s /usr/lib/python2.7/site-packages/numpy-1.8.0-py2.7.egg-info $VIRTUAL_ENV/lib/python2.7/site-packages/numpy-1.8.0-py2.7.egg-info
    64-bit Fedora Linux:
        ln -s /usr/lib64/python2.7/site-packages/numpy $VIRTUAL_ENV/lib/python2.7/site-packages/numpy
        ln -s /usr/lib64/python2.7/site-packages/numpy-1.8.0-py2.7.egg-info $VIRTUAL_ENV/lib/python2.7/site-packages/numpy-1.8.0-py2.7.egg-info
    Ubuntu:
        ln -s /usr/lib/python2.7/dist-packages/numpy $VIRTUAL_ENV/lib/python2.7/site-packages/numpy
        ln -s /usr/lib/python2.7/dist-packages/numpy-1.8.0-py2.7.egg-info $VIRTUAL_ENV/lib/python2.7/site-packages/numpy-1.8.0-py2.7.egg-info
    Windows 7/8 (As Administrator):
        mklink /D %VIRTUAL_ENV%\Lib\site-packages\numpy C:\Python27\Lib\site-packages\numpy
        mklink /D %VIRTUAL_ENV%\Lib\site-packages\numpy-1.8.0-py2.7.egg-info C:\Python27\Lib\site-packages\numpy-1.8.0-py2.7.egg-info

Then, with the virtualenv enabled, run:
    pip install sPyNNaker


pyNN.spiNNaker support
======================
If you want to be able to use sPyNNaker like the other PyNN simulators,
e.g. calling "import pyNN.spiNNaker as p" at the top of your pyNN scripts,
you will need to do one of the following, depending on how you have installed
pyNN.

pyNN installed for all users:
    sudo pip install pyNN-spiNNaker

pyNN installed for only yourself:
    pip install pyNN-spiNNaker --user

pyNN installed in a virtualenv:
    pip install pyNN-spiNNaker


Developer Installation
======================
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
