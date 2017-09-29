# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

APP = robot_motor_control
BUILD_DIR = build/
SOURCES = robot_motor_control/robot_motor_control.c

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
CFLAGS += -I$(abspath $(SOURCE_DIR))
vpath %.c $(abspath $(SOURCE_DIR)/robot_motor_control)
vpath %.h $(abspath $(SOURCE_DIR))
include $(NEURAL_MODELLING_DIRS)/src/common.mk

.PHONY: all clean
