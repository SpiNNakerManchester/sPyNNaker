# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif
# If NEURAL_MODELLING_DIRS is not defined, this is never reached

_MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_CURRENT_DIR := $(dir $(_MAKEFILE_PATH))
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(_CURRENT_DIR)../spynnaker/pyNN/model_binaries/)/
endif

# Rules will use the converted version so fthe common files
COMMON_RAW_DIR := $(NEURAL_MODELLING_DIRS)/common
COMMON_MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/common_modified/
COMMON_DICT_FILE := $(NEURAL_MODELLING_DIRS)/common_modified/common.dict
# Add to include flag
CFLAGS += -I $(COMMON_MODIFIED_DIR)
# Add to list or prerequirements for rule to build o files
COPIED_DIRS += $(COMMON_MODIFIED_DIR)

# local.mk includes rules for converting in Sources and local files
include $(SPINN_DIRS)/make/local.mk

# Copy the common files
$(COMMON_MODIFIED_DIR) $(COMMON_DICT_FILE): $(COMMON_RAW_DIR)
	python -m spinn_utilities.make_tools.convertor $(COMMON_RAW_DIR) $(COMMON_MODIFIED_DIR) $(COMMON_DICT_FILE) neural_modelling_common

test:
	echo $(COMMON_MODIFIED_DIR)

