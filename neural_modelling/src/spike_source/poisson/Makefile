# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

APP = spike_source_poisson
BUILD_DIR = build/
SOURCES = common/out_spikes.c spike_source/poisson/spike_source_poisson.c

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
CFLAGS += -I$(abspath $(SOURCE_DIR))
vpath %.c $(abspath $(SOURCE_DIR)/common):$(abspath $(SOURCE_DIR)/spike_source/poisson)
vpath %.h $(abspath $(SOURCE_DIR))
include $(NEURAL_MODELLING_DIRS)/src/common.mk

.PHONY: all clean
