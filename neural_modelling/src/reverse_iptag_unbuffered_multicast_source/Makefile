##------------------------------------------------------------------------------
##
## Makefile        Makefile for a simple SpiNNaker application
##
## Copyright (C)   The University of Manchester - 2013
##
## Author          Steve Temple, APT Group, School of Computer Science
##
## Email           temples@cs.man.ac.uk
##
##------------------------------------------------------------------------------

# Makefile for a simple SpiNNaker application. This will compile
# a single C source file into an APLX file which can be loaded onto
# SpiNNaker. It will link with either a 'bare' SARK library or a
# combined SARK/API library.

# The options below can be overridden from the command line or via
# environment variables. For example, to compile and link "my_example.c"
# with the ARM tools and generate ARM (as opposed to Thumb) code
#
# make APP=my_example GNU=0 THUMB=0

# Name of app (derived from C source - eg sark.c)

APP = reverse_iptag_multicast_source$(EXT)
DIRS = ..
BUILDDIR = build
DEBUG = PRODUCTION_CODE

#-------------------------------------------------------------------------------

#CFLAGS += -Wall -Wextra -DDEBUG -Ofast
CFLAGS += -Wall -Wextra -D$(DEBUG) -Ofast

#-------------------------------------------------------------------------------

# Build the application

# List of objects making up the application. If there are other files
# in the application, add their object file names to this variable.


OBJECTS = reverse_iptag_multicast_source.o ../common/spin1-api-configuration.o ../common/configuration.o ../common/out_spikes.o ../common/recording.o

# Include common make file stuff
include ../Makefile.depend
