# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif
# If NEURAL_MODELLING_DIRS is not defined, this is never reached

_MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_CURRENT_DIR := $(dir $(_MAKEFILE_PATH))
#SOURCE_DIR := $(abspath $(CURRENT_DIR))
#SOURCE_DIRS += $(SOURCE_DIR)
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(_CURRENT_DIR)../../spynnaker/pyNN/model_binaries/)/
endif

include $(NEURAL_MODELLING_DIRS)/commoncopy.mk
COPIED_DIRS += $(COMMON_MODIFIED_DIR)

include $(SPINN_DIRS)/make/local.mk

CFLAGS += -I $(COMMON_MODIFIED_DIR)


test:
	# $(_COMMON_RANGE_FILE)

