# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif
# If NEURAL_MODELLING_DIRS is not defined, this is never reached

_MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_CURRENT_DIR := $(dir $(_MAKEFILE_PATH))
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(_CURRENT_DIR)../../spynnaker/pyNN/model_binaries/)/
endif

# local.mk includes rules for converting in Sources and local files
include $(SPINN_DIRS)/make/local.mk

# Rules will use the converted version so fthe common files
COMMON_MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/src/common_modified/
# Add to include flag
CFLAGS += -I $(COMMON_MODIFIED_DIR)
# Add to list or prerequirements for rule to build o files
COPIED_DIRS += $(COMMON_MODIFIED_DIR)

# Copy the common files
RAW_DIR :=  $(NEURAL_MODELLING_DIRS)/src/common/
CONVERT_DIR := $(COMMON_MODIFIED_DIR)
SUMMARY_DICT := $(COMMON_MODIFIED_DIR)common.dict
include $(SPINN_DIRS)/make/convert.mk

test:
	echo $(ALL_TARGETS)

