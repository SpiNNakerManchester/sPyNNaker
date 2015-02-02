APP = $(notdir $(CURDIR))
BUILD_DIR = build/
SOURCE_DIR = $(NEURAL_MODELLING_DIRS)/src
MODEL_OBJS = $(SOURCE_DIR)/neuron/models/neuron_model_lif_curr_impl.o $(SOURCE_DIR)/neuron/plasticity/synapse_dynamics_static_impl.o
NEURON_MODEL_H = ../../models/neuron_model_lif_curr_impl.h
SYNAPSE_TYPE_H = ../../synapse_types/synapse_types_exponential_impl.h
APPLICATION_MAGIC_NUMBER = 0xAC1

include ../Makefile.common
