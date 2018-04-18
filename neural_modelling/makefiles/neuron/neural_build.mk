# See Notes in sPyNNaker/neural_modelling/CHANGES_April_2018

# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif

# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif
#Check NEURAL_MODELLING_DIRS
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
ifneq ($(NEURAL_MODELLING_DIRS)/makefiles/neuron/neural_build.mk, $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

# Set logging levels
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

# Define the directories
SRC_DIR := $(NEURAL_MODELLING_DIRS)/src/
	# Ok to share modified files between builds
MODIFIED_DIR := $(NEURAL_MODELLING_DIRS)/modified_src/
	# Need to build each neuron seperately or complier gets confused
BUILD_DIR := $(NEURAL_MODELLING_DIRS)/builds/$(APP)/
APP_OUTPUT_DIR :=  $(abspath $(dir $(MAKEFILE_PATH))../../../spynnaker/pyNN/model_binaries/)
LOG_DICT_FILE := $(MODIFIED_DIR)log_dict.dict

# Check required inputs and point them to modified sources
ifndef ADDITIONAL_INPUT_H
    ADDITIONAL_INPUT_H = $(MODIFIED_DIR)neuron/additional_inputs/additional_input_none_impl.h
endif

ifndef NEURON_MODEL
    $(error NEURON_MODEL is not set.  Please choose a neuron model to compile)
else
    NEURON_MODEL := $(MODIFIED_DIR)$(NEURON_MODEL)
    NEURON_MODEL_O := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(NEURON_MODEL))
endif

ifndef NEURON_MODEL_H
    $(error NEURON_MODEL_H is not set.  Please select a neuron model header file)
else
    NEURON_MODEL_H := $(MODIFIED_DIR)$(NEURON_MODEL_H)
endif

ifndef INPUT_TYPE_H
    $(error INPUT_TYPE_H is not set.  Please select an input type header file)
else
    INPUT_TYPE_H := $(MODIFIED_DIR)$(INPUT_TYPE_H)
endif

ifndef THRESHOLD_TYPE_H
    $(error THRESHOLD_TYPE_H is not set.  Please select a threshold type header file)
else
    THRESHOLD_TYPE_H := $(MODIFIED_DIR)$(THRESHOLD_TYPE_H)
endif

ifndef SYNAPSE_TYPE_H
    $(error SYNAPSE_TYPE_H is not set.  Please select a synapse type header file)
else
    SYNAPSE_TYPE_H := $(MODIFIED_DIR)$(SYNAPSE_TYPE_H)
endif

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
else
    SYNAPSE_DYNAMICS := $(MODIFIED_DIR)$(SYNAPSE_DYNAMICS)
endif

ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE := $(MODIFIED_DIR)$(WEIGHT_DEPENDENCE)
    WEIGHT_DEPENDENCE_O := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(WEIGHT_DEPENDENCE))
endif

ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE := $(MODIFIED_DIR)$(TIMING_DEPENDENCE)
    TIMING_DEPENDENCE_O := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(TIMING_DEPENDENCE))
endif

SYNGEN_ENABLED = 1

ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS := $(MODIFIED_DIR)neuron/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNGEN_ENABLED = 0
else
    SYNAPTOGENESIS_DYNAMICS := $(MODIFIED_DIR)$(SYNAPTOGENESIS_DYNAMICS)
endif

# List all the sources
SOURCES = $(MODIFIED_DIR)common/out_spikes.c \
          $(MODIFIED_DIR)neuron/c_main.c \
          $(MODIFIED_DIR)neuron/synapses.c \
          $(MODIFIED_DIR)neuron/neuron.c \
          $(MODIFIED_DIR)neuron/spike_processing.c \
          $(MODIFIED_DIR)neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          $(NEURON_MODEL) $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) $(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS)

# Convert the sources into Objects
OBJECTS := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(SOURCES))

#Build rules
all: $(APP_OUTPUT_DIR)$(APP).aplx

include $(SPINN_DIRS)/make/Makefile.common

# TODO may need a fourth pthyon parameter
# Rules to convert the source files
$(MODIFIED_DIR)%.c: $(SRC_DIR)%.c
	python -m spinn_utilities.make_tools.convertor $(SRC_DIR) $(MODIFIED_DIR) $(LOG_DICT_FILE) 

$(LOG_DICT_FILE): $(SRC_DIR)
	python -m spinn_utilities.make_tools.convertor $(SRC_DIR) $(MODIFIED_DIR) $(LOG_DICT_FILE) 

LIBRARIES += -lspinn_frontend_common -lspinn_common -lm
FEC_DEBUG := PRODUCTION_CODE
PROFILER := PROFILER_DISABLED

# Run md5sum on application name and extract first 8 bytes
SHELL = bash
APPLICATION_NAME_HASH = $(shell echo -n "$(APP)" | (md5sum 2>/dev/null || md5) | cut -c 1-8)

CFLAGS += -Wall -Wextra -D$(FEC_DEBUG) -D$(PROFILER) $(OTIME) -DAPPLICATION_NAME_HASH=0x$(APPLICATION_NAME_HASH)
CFLAGS += -I $(SPINN_DIRS)/include
CFLAGS += -I $(MODIFIED_DIR)

# Simple build rules
$(BUILD_DIR)%.o: $(MODIFIED_DIR)%.c $(LOG_DICT_FILE)
	# Simple
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

# Synapese build rules
SYNAPSE_TYPE_COMPILE = $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -include $(SYNAPSE_TYPE_H)

$(BUILD_DIR)neuron/c_main.o: $(MODIFIED_DIR)neuron/c_main.c $(LOG_DICT_FILE)
	#c_main.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/synapses.o: $(MODIFIED_DIR)neuron/synapses.c $(LOG_DICT_FILE)
	#synapses.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/spike_processing.o: $(MODIFIED_DIR)neuron/spike_processing.c $(LOG_DICT_FILE)
	#spike_processing.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_fixed_impl.o: $(MODIFIED_DIR)neuron/population_table/population_table_fixed_impl.c $(LOG_DICT_FILE)
	#population_table/population_table_fixed_impln.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_binary_search_impl.o: $(MODIFIED_DIR)neuron/population_table/population_table_binary_search_impl.c $(LOG_DICT_FILE)
	#population_table/population_table_binary_search_impl
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

#STDP Build rules If and only if STDP used
STDP_ENABLED = 0
SYNAPSE_DYNAMICS_O := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(SYNAPSE_DYNAMICS))
SYNAPTOGENESIS_DYNAMICS_O := $(patsubst $(MODIFIED_DIR)%.c,$(BUILD_DIR)%.o,$(SYNAPTOGENESIS_DYNAMICS))

ifneq ($(SYNAPSE_DYNAMICS), $(MODIFIED_DIR)neuron/plasticity/synapse_dynamics_static_impl.c)
    ifdef TIMING_DEPENDENCE_H
	TIMING_DEPENDENCE_H := $(MODIFIED_DIR)$(TIMING_DEPENDENCE_H)
    else
        $(error TIMING_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS != neuron/plasticity/synapse_dynamics_static_impl.c)
    endif
    ifdef WEIGHT_DEPENDENCE_H
	WEIGHT_DEPENDENCE_H := $(MODIFIED_DIR)$(WEIGHT_DEPENDENCE_H)
    else
        $(error WEIGHT_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS != neuron/plasticity/synapse_dynamics_static_impl.c)
    endif

    STDP_ENABLED = 1

    STDP_INCLUDES:= -include $(SYNAPSE_TYPE_H) -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H)
    STDP_COMPILE = $(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) $(STDP_INCLUDES)

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS) $(LOG_DICT_FILE)
	# SYNAPSE_DYNAMICS_O stdp
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(LOG_DICT_FILE)
	# SYNAPTOGENESIS_DYNAMICS_O stdp
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(BUILD_DIR)neuron/plasticity/common/post_events.o: $(MODIFIED_DIR)neuron/plasticity/common/post_events.c
	# plasticity/common/post_events.c
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

 else
    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(LOG_DICT_FILE)
	# $(SYNAPTOGENESIS_DYNAMICS) Synapese
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS) $(LOG_DICT_FILE)
	# SYNAPSE_DYNAMICS_O Synapese
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

endif

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE) $(SYNAPSE_TYPE_H)
	# WEIGHT_DEPENDENCE_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H)
	# TIMING_DEPENDENCE_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H)\
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(NEURON_MODEL_O): $(NEURON_MODEL)
	# NEURON_MODEL_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(NEURON_DEBUG) \
	        $(CFLAGS) -o $@ $<

$(BUILD_DIR)neuron/neuron.o: $(MODIFIED_DIR)neuron/neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H) $(LOG_DICT_FILE)
	# neuron.o
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      -include $(NEURON_MODEL_H) \
	      -include $(SYNAPSE_TYPE_H) \
	      -include $(INPUT_TYPE_H) \
	      -include $(THRESHOLD_TYPE_H) \
	      -include $(ADDITIONAL_INPUT_H) \
	      -o $@ $<

# Tidy and cleaning dependencies
clean:
	$(RM) $(OBJECTS) $(APP_OUTPUT_DIR)$(APP).aplx
	rm -rf $(BUILD_DIR)
	rm -rf $(MODIFIED_DIR)

test: 
	# $(STDP_ENABLED)
	# $(STDP_COMPILE)

