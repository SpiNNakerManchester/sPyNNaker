# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

APP = delay_extension
BUILD_DIR = build/
SOURCES = delay_extension/delay_extension.c

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
CFLAGS += -I$(abspath $(SOURCE_DIR))
vpath %.c $(abspath $(SOURCE_DIR)/delay_extension)
vpath %.h $(abspath $(SOURCE_DIR))
include $(NEURAL_MODELLING_DIRS)/src/common.mk

.PHONY: all clean
