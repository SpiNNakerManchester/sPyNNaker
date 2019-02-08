# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif
# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif
#Check NEURAL_MODELLING_DIRS
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CHECK_PATH := $(NEURAL_MODELLING_DIRS)/makefiles/neural_support.mk
ifneq ($(CHECK_PATH), $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

# APP name for a and dict files
ifndef APP
    $(error APP is not set.  Please define APP)
endif

# Define the directories
SRC_DIR := $(NEURAL_MODELLING_DIRS)/src/
SOURCE_DIRS += $(SRC_DIR)
MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/modified_src/
BUILD_DIR := $(NEURAL_MODELLING_DIRS)/builds/$(APP)/
APP_OUTPUT_DIR :=  $(abspath $(dir $(MAKEFILE_PATH))../../spynnaker/pyNN/model_binaries)/

include $(SPINN_DIRS)/make/local.mk

