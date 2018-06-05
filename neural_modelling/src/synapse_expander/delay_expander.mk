APP = delay_expander
BUILD_DIR = build/
SOURCES = rng.c param_generator.c connection_generator.c delay_expander.c

include ../common.mk

CFLAGS += -I$(NEURAL_MODELLING_DIRS)/src
