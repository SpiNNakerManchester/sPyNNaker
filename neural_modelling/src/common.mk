# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CHECK_PATH := $(NEURAL_MODELLING_DIRS)/src/common.mk
ifneq ($(CHECK_PATH), $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
include $(SPINN_DIRS)/make/Makefile.SpiNNFrontEndCommon

# Cancel all rules for RCS and SCCS; *definitely* not using them!
%: %,v
%: RCS/%,v
%: RCS/%
%: s.%
%: SCCS/s.%
