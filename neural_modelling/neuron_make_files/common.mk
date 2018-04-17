# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif

# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    NEURON_DEBUG = LOG_DEBUG
    SYNAPSE_DEBUG = LOG_DEBUG
    PLASTIC_DEBUG = LOG_DEBUG
endif

ifndef NEURON_DEBUG
    NEURON_DEBUG = LOG_INFO
endif

ifndef SYNAPSE_DEBUG
    SYNAPSE_DEBUG = LOG_INFO
endif

ifndef PLASTIC_DEBUG
    PLASTIC_DEBUG = LOG_INFO
endif

#POPULATION_TABLE_IMPL := fixed
POPULATION_TABLE_IMPL := binary_search

# Variables used the converted version of the common files
COMMON_RAW_DIR := $(NEURAL_MODELLING_DIRS)/common/
COMMON_MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/common_modified/
COMMON_DICT_FILE := $(NEURAL_MODELLING_DIRS)/common_modified/common.dict
COMMON_BUILD_DIR = $(NEURAL_MODELLING_DIRS)/common_build/
# Add to list or prerequirements for rule to build o files
C_FILES_MODIFIED += $(COMMON_DICT_FILE)
NEURON_RAW_DIR := $(NEURAL_MODELLING_DIRS)/neuron/
NEURON_MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/neuron_modified/
NEURON_DICT_FILE := $(NEURAL_MODELLING_DIRS)/neuron_modified/neuron.dict
NEURON_BUILD_DIR = $(NEURAL_MODELLING_DIRS)/neuron_build/
# Add to list or prerequirements for rule to build o files
C_FILES_MODIFIED += $(NEURON_DICT_FILE)
#locaTION FOR ELF AND OTHER FILES
BUILD_DIR = $(NEURAL_MODELLING_DIRS)/build/


ifndef ADDITIONAL_INPUT_H
    ADDITIONAL_INPUT_H = $(NEURON_MODIFIED_DIR)additional_inputs/additional_input_none_impl.h
endif

ifndef NEURON_MODEL
    $(error NEURON_MODEL is not set.  Please choose a neuron model to compile)
else
    NEURON_MODEL := $(NEURON_MODIFIED_DIR)$(NEURON_MODEL)
    NEURON_MODEL_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)%.o,$(NEURON_MODEL))
endif

ifndef NEURON_MODEL_H
    $(error NEURON_MODEL_H is not set.  Please select a neuron model header file)
else
    NEURON_MODEL_H := $(NEURON_MODIFIED_DIR)$(NEURON_MODEL_H)
endif

ifndef INPUT_TYPE_H
    $(error INPUT_TYPE_H is not set.  Please select an input type header file)
else
    INPUT_TYPE_H := $(NEURON_MODIFIED_DIR)$(INPUT_TYPE_H)
endif

ifndef THRESHOLD_TYPE_H
    $(error THRESHOLD_TYPE_H is not set.  Please select a threshold type header file)
else
    THRESHOLD_TYPE_H := $(NEURON_MODIFIED_DIR)$(THRESHOLD_TYPE_H)
endif

ifndef SYNAPSE_TYPE_H
    $(error SYNAPSE_TYPE_H is not set.  Please select a synapse type header file)
else
    SYNAPSE_TYPE_H := $(NEURON_MODIFIED_DIR)$(SYNAPSE_TYPE_H)
endif

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
else
    SYNAPSE_DYNAMICS := $(NEURON_MODIFIED_DIR)$(SYNAPSE_DYNAMICS)
endif

ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE := $(NEURON_MODIFIED_DIR)($(WEIGHT_DEPENDENCE)
    WEIGHT_DEPENDENCE_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)$%.o,$(WEIGHT_DEPENDENCE))
endif

ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE_O := $(NEURON_MODIFIED_DIR)$(TIMING_DEPENDENCE)
    TIMING_DEPENDENCE_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)$%.o,$(TIMING_DEPENDENCE))
endif

SYNGEN_ENABLED = 1

ifndef SYNAPTOGENESIS_DYNAMICS_H
    SYNAPTOGENESIS_DYNAMICS_H = $(NEURON_MODIFIED_DIR)synaptogenesis_dynamics.h
    SYNGEN_ENABLED = 0
endif

ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS = $(NEURON_MODIFIED_DIR)structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNGEN_ENABLED = 0
endif

_MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_CURRENT_DIR := $(dir $(MAKEFILE_PATH))
#SOURCE_DIR := $(abspath $(CURRENT_DIR))
#SOURCE_DIRS += $(SOURCE_DIR)
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(_CURRENT_DIR)../../spynnaker/pyNN/model_binaries/)/
endif

NEURON_O = $(NEURON_BUILD_DIR)neuron.o

SOURCES = $(COMMON_MODIFIED_DIR)out_spikes.c \
          $(NEURON_MODIFIED_DIR)c_main.c \
          $(NEURON_MODIFIED_DIR)synapses.c \
          $(NEURON_MODIFIED_DIR)neuron.c \
          $(NEURON_MODIFIED_DIR)spike_processing.c \
          $(NEURON_MODIFIED_DIR)population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          $(NEURON_MODEL) $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) $(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS)

# Convert the objs into the correct format to work here
OBJECTS := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)%.o,$(SOURCES))
OBJECTS := $(patsubst $(COMMON_MODIFIED_DIR)%.c,$(COMMON_BUILD_DIR)%.o,$(OBJECTS))

#Build rules
all: $(APP_OUTPUT_DIR)$(APP).aplx

include $(SPINN_DIRS)/make/Makefile.common

# Copy the common files
$(COMMON_DICT_FILE): $(COMMON_RAW_DIR)                                                                          # Extra tag as this is a library
	python -m spinn_utilities.make_tools.convertor $(COMMON_RAW_DIR) $(COMMON_MODIFIED_DIR) $(COMMON_DICT_FILE) neural_modelling_common

	# While the called python copied the whole directory the individual rule is required for the makerule chain
$(COMMON_MODIFIED_DIR)%.c:  $(COMMON_RAW_DIR)%.c                                                                  # Extra tag as this is a library%.c
	python -m spinn_utilities.make_tools.convertor $(COMMON_RAW_DIR) $(COMMON_MODIFIED_DIR) $(COMMON_DICT_FILE) neural_modelling_common

# Copy the neuron files
$(NEURON_DICT_FILE): $(NEURON_RAW_DIR)
	python -m spinn_utilities.make_tools.convertor $(NEURON_RAW_DIR) $(NEURON_MODIFIED_DIR) $(NEURON_DICT_FILE) 

	# While the called python copied the whole directory the individual rule is required for the makerule chain
$(NEURON_MODIFIED_DIR)%.c: $(NEURON_RAW_DIR)%.c
	python -m spinn_utilities.make_tools.convertor $(NEURON_RAW_DIR) $(NEURON_MODIFIED_DIR) $(NEURON_DICT_FILE) 


LIBRARIES += -lspinn_frontend_common -lspinn_common -lm
FEC_DEBUG := PRODUCTION_CODE
PROFILER := PROFILER_DISABLED

# Run md5sum on application name and extract first 8 bytes
SHELL = bash
APPLICATION_NAME_HASH = $(shell echo -n "$(APP)" | (md5sum 2>/dev/null || md5) | cut -c 1-8)

CFLAGS += -Wall -Wextra -D$(FEC_DEBUG) -D$(PROFILER) $(OTIME) -DAPPLICATION_NAME_HASH=0x$(APPLICATION_NAME_HASH)
CFLAGS += -I $(SPINN_DIRS)/include
CFLAGS += -I $(COMMON_MODIFIED_DIR)
INCLUDE_NEURON_HEADERS = -I $(NEURON_MODIFIED_DIR)
INCLUDE_PLASTICITY_HEADERS = $(INCLUDE_NEURON_HEADERS) -I $(NEURON_MODIFIED_DIR)plasticity

# Simple build rules
$(COMMON_BUILD_DIR)%.o: $(COMMON_MODIFIED_DIR)%.c $(C_FILES_MODIFIED)
	# Simple
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

$(NEURON_BUILD_DIR)%.o: $(NEURON_MODIFIED_DIR)%.c $(C_FILES_MODIFIED)
	# Simple
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

# Synapese build rules
SYNAPSE_TYPE_COMPILE:= $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) $(INCLUDE_PLASTICITY_HEADERS) -DSTDP_ENABLED=$(STDP_ENABLED) -include $(SYNAPSE_TYPE_H)

$(NEURON_BUILD_DIR)c_main.o: $(NEURON_MODIFIED_DIR)c_main.c $(C_FILES_MODIFIED) 
	#c_main.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(NEURON_BUILD_DIR)synapses.o: $(NEURON_MODIFIED_DIR)synapses.c $(C_FILES_MODIFIED) 
	#synapses.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(NEURON_BUILD_DIR)spike_processing.o: $(NEURON_MODIFIED_DIR)spike_processing.c $(C_FILES_MODIFIED) 
	#spike_processing.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(NEURON_BUILD_DIR)population_table/population_table_fixed_impl.o: $(NEURON_MODIFIED_DIR)population_table/population_table_fixed_impl.c $(C_FILES_MODIFIED) 
	#population_table/population_table_fixed_impln.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(NEURON_BUILD_DIR)population_table/population_table_binary_search_impl.o: $(NEURON_MODIFIED_DIR)population_table/population_table_binary_search_impl.c $(C_FILES_MODIFIED) 
	#population_table/population_table_binary_search_impl
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

#STDP Build rules If and only if STDP used
STDP_ENABLED = 0

ifneq ($(SYNAPSE_DYNAMICS), $(NEURON_MODIFIED_DIR)/plasticity/synapse_dynamics_static_impl.c)
    STDP_ENABLED = 1

    STDP_INCLUDES:= $(INCLUDE_PLASTICITY_HEADERS) -include $(SYNAPSE_TYPE_H) -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H)
    STDP_COMPILE = $(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) $(STDP_INCLUDES)

    SYNAPSE_DYNAMICS_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)%.o,$(SYNAPSE_DYNAMICS))

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS) $(C_FILES_MODIFIED) 
	# SYNAPSE_DYNAMICS_O
	# $(WEIGHT_DEPENDENCE_H)
	# $(TIMING_DEPENDENCE_H)
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    SYNAPTOGENESIS_DYNAMICS_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)%.o,$(SYNAPTOGENESIS_DYNAMICS))

    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(C_FILES_MODIFIED) 
	# SYNAPTOGENESIS_DYNAMICS_O stdp
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(NEURON_BUILD_DIR)/plasticity/common/post_events.o: $(NEURON_MODIFIED_DIR)/plasticity/common/post_events.c
	# plasticity/common/post_events.c
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

 else
    SYNAPTOGENESIS_DYNAMICS_O := $(patsubst $(NEURON_MODIFIED_DIR)%.c,$(NEURON_BUILD_DIR)%.o,$(SYNAPTOGENESIS_DYNAMICS))

    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(C_FILES_MODIFIED) 
	# $(SYNAPTOGENESIS_DYNAMICS) SYNAPSE
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

endif

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE) $(SYNAPSE_TYPE_H)
	# WEIGHT_DEPENDENCE_O
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        $(INCLUDE_PLASTICITY_HEADERS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H)
	# TIMING_DEPENDENCE_O
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        $(INCLUDE_PLASTICITY_HEADERS) \
	        -include $(SYNAPSE_TYPE_H)\
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(NEURON_MODEL_O): $(NEURON_MODEL)
	# NEURON_MODEL_O
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(NEURON_DEBUG) \
	        $(CFLAGS) -o $@ $<

$(NEURON_O): $(NEURON_MODIFIED_DIR)neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H)
	# NEURON_O
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"neuron.c\" -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      $(INCLUDE_NEURON_HEADERS) \
	      -include $(NEURON_MODEL_H) \
	      -include $(SYNAPSE_TYPE_H) \
	      -include $(INPUT_TYPE_H) \
	      -include $(THRESHOLD_TYPE_H) \
	      -include $(ADDITIONAL_INPUT_H) \
	      -include $(SYNAPTOGENESIS_DYNAMICS_H) -o $@ $<

# Tidy and cleaning dependencies
clean:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt $(APP_OUTPUT_DIR)$(APP).aplx
	rm -rf $(COMMON_BUILD_DIR)
	rm -rf $(NEURON_BUILD_DIR)
	rm -rf $(COMMON_MODIFIED_DIR)
	rm -rf $(NEURON_MODIFIED_DIR)



