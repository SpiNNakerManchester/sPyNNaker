APP = $(notdir $(CURDIR))
BUILD_DIR = build/
MODEL_OBJS = $(SOURCE_DIRS)/neuron/models/neuron_model_lif_curr_impl.o \
             $(SOURCE_DIRS)/neuron/plasticity/stp/synapse_dynamics_stp.o \
             $(SOURCE_DIRS)/neuron/plasticity/common/maths.o \
             $(SOURCE_DIRS)/neuron/plasticity/stp/rules/tsodyks_markram.o
NEURON_MODEL_H = ../../models/neuron_model_lif_curr_impl.h
SYNAPSE_TYPE_H = ../../synapse_types/synapse_types_exponential_impl.h
STP_RULE_H = ../../plasticity/stp/rules/tsodyks_markram_impl.h

include ../Makefile.common
