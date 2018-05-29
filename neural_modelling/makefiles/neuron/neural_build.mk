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
# Path flag to replace with the modified dir  (abspath drops the final /)
NEURON_DIR := $(abspath $(NEURAL_MODELLING_DIRS)/src)
# For historical reasons we support the variable SOURCE_DIR but its use is not encouraged
SOURCE_DIR := $(NEURON_DIR)
MODIFIED_DIR := $(abspath $(NEURAL_MODELLING_DIRS)/modified_src)
	# Need to build each neuron seperately or complier gets confused
# BUILD_DIR and APP_OUTPUT_DIR end with a / for historictical/ shared reasons
    # abspath strips of the final / so save to add one on after
ifndef BUILD_DIR
    BUILD_DIR := $(NEURAL_MODELLING_DIRS)/builds/$(APP)/
endif
BUILD_DIR := $(abspath $(BUILD_DIR))/
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR :=  $(NEURAL_MODELLING_DIRS)/../spynnaker/pyNN/model_binaries
endif
APP_OUTPUT_DIR :=  $(abspath $(APP_OUTPUT_DIR))/

MODIFIED_DICT_FILE := $(MODIFIED_DIR)/log_dict.dict
LOG_DICT_FILES += $(wildcard $(SPINN_DIRS)/lib/*.dict)
LOG_DICT_FILES += $(MODIFIED_DICT_FILE)
# If the LOG_DICT_FILES are up to date we know the c code has been modifed 
C_FILES_MODIFIED = $(LOG_DICT_FILES)
APP_DICT_FILE = $(APP_OUTPUT_DIR)$(APP).dict

# function to convert a path with NEURON_DIR to use MODIFIED_DIR instead
# $1 is the first parameter passed in
# extra_convert_to_modified can be used to convert other scrource directories to their modified
# patsubst is pattern substitution so does nothing if path does not start with NEURON_DIR
# abspath is used to remove double /, any ../ and any trailing / 
ifdef extra_convert_to_modified
define convert_to_modified
$(abspath $(patsubst $(NEURON_DIR)/%,$(MODIFIED_DIR)/%,$(call extra_convert_to_modified, $(1))))
endef
else
define convert_to_modified
$(abspath $(patsubst $(NEURON_DIR)/%,$(MODIFIED_DIR)/%,$(1)))
endef
endif

# function to convert c file to a object file in the build dir
# $1 is the first parameter passed in
# extra_convert_to_object can be used to convert other modified directories
# patsubst is pattern substitution so does nothing if path does not start with $(MODIFIED_DIR)/
# abspath is used to remove double /, any ../ and any trailing /
# BUILD_DIR ends with a / for historictical/ shared reasons

ifdef extra_convert_to_object
define convert_to_object
$(abspath $(patsubst $(MODIFIED_DIR)/%.c, $(BUILD_DIR)%.o, $(call extra_convert_to_object, $(1))))
endef
else
define convert_to_object
$(abspath $(patsubst $(MODIFIED_DIR)/%.c, $(BUILD_DIR)%.o, $(1)))
endef
endif

# Check required inputs and point them to modified sources
ifndef ADDITIONAL_INPUT_H
    ADDITIONAL_INPUT_H = $(MODIFIED_DIR)/neuron/additional_inputs/additional_input_none_impl.h
else
    ADDITIONAL_INPUT_H := $(call convert_to_modified, $(ADDITIONAL_INPUT_H))
endif

ifndef NEURON_MODEL
    $(error NEURON_MODEL is not set.  Please choose a neuron model to compile)
else
    NEURON_MODEL :=  $(call convert_to_modified, $(NEURON_MODEL))
    NEURON_MODEL_O := $(call convert_to_object ,$(NEURON_MODEL))
endif

ifndef NEURON_MODEL_H
    $(error NEURON_MODEL_H is not set.  Please select a neuron model header file)
else
    NEURON_MODEL_H := $(call convert_to_modified, $(NEURON_MODEL_H))
endif

ifndef INPUT_TYPE_H
    $(error INPUT_TYPE_H is not set.  Please select an input type header file)
else
    INPUT_TYPE_H := $(call convert_to_modified, $(INPUT_TYPE_H))
endif

ifndef THRESHOLD_TYPE_H
    $(error THRESHOLD_TYPE_H is not set.  Please select a threshold type header file)
else
    THRESHOLD_TYPE_H := $(call convert_to_modified, $(THRESHOLD_TYPE_H))
endif

ifndef SYNAPSE_TYPE_H
    $(error SYNAPSE_TYPE_H is not set.  Please select a synapse type header file)
else
    SYNAPSE_TYPE_H := $(call convert_to_modified, $(SYNAPSE_TYPE_H))
endif

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
else
    SYNAPSE_DYNAMICS := $(call convert_to_modified, $(SYNAPSE_DYNAMICS))
endif

ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE := $(call convert_to_modified, $(WEIGHT_DEPENDENCE))
    WEIGHT_DEPENDENCE_O := $(call convert_to_object, $(WEIGHT_DEPENDENCE))
endif

ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE := $(call convert_to_modified, $(TIMING_DEPENDENCE))
    TIMING_DEPENDENCE_O := $(call convert_to_object, $(TIMING_DEPENDENCE))
endif

SYNGEN_ENABLED = 1

ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS := $(MODIFIED_DIR)/neuron/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNGEN_ENABLED = 0
else
    SYNAPTOGENESIS_DYNAMICS := $(call convert_to_modified, $(SYNAPTOGENESIS_DYNAMICS))
endif

# List all the sources
SOURCES = $(MODIFIED_DIR)/common/out_spikes.c \
          $(MODIFIED_DIR)/neuron/c_main.c \
          $(MODIFIED_DIR)/neuron/synapses.c \
          $(MODIFIED_DIR)/neuron/neuron.c \
          $(MODIFIED_DIR)/neuron/spike_processing.c \
          $(MODIFIED_DIR)/neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          $(NEURON_MODEL) $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) $(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS)

# Convert the sources into Objects
OBJECTS := $(call convert_to_object, $(SOURCES))

#Build rules
all: $(APP_OUTPUT_DIR)$(APP).aplx $(APP_DICT_FILE)

include $(SPINN_DIRS)/make/spinnaker_tools.mk

# Rules to convert the source files
$(MODIFIED_DIR)%.c: $(NEURON_DIR)%.c
	python -m spinn_utilities.make_tools.converter $(NEURON_DIR) $(MODIFIED_DIR) $(MODIFIED_DICT_FILE)

$(MODIFIED_DIR)%.h: $(NEURON_DIR)%.c
	python -m spinn_utilities.make_tools.converter $(NEURON_DIR) $(MODIFIED_DIR) $(MODIFIED_DICT_FILE)

$(MODIFIED_DICT_FILE): $(NEURON_DIR)
	python -m spinn_utilities.make_tools.converter $(NEURON_DIR) $(MODIFIED_DIR) $(MODIFIED_DICT_FILE)

LIBRARIES += -lspinn_frontend_common -lspinn_common -lm
FEC_DEBUG := PRODUCTION_CODE
PROFILER := PROFILER_DISABLED

# Run md5sum on application name and extract first 8 bytes
SHELL = bash
APPLICATION_NAME_HASH = $(shell echo -n "$(APP)" | (md5sum 2>/dev/null || md5) | cut -c 1-8)

CFLAGS += -Wall -Wextra -D$(FEC_DEBUG) -D$(PROFILER) $(OTIME) -DAPPLICATION_NAME_HASH=0x$(APPLICATION_NAME_HASH)
CFLAGS += -I $(SPINN_DIRS)/include
CFLAGS += -I $(MODIFIED_DIR)
FEC_OPT = $(OSPACE)

# Simple build rules
$(BUILD_DIR)%.o: $(MODIFIED_DIR)/%.c $(C_FILES_MODIFIED)
	# Simple
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

# Synapese build rules
SYNAPSE_TYPE_COMPILE = $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -include $(SYNAPSE_TYPE_H)

$(BUILD_DIR)neuron/c_main.o: $(MODIFIED_DIR)/neuron/c_main.c $(C_FILES_MODIFIED)
	#c_main.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/synapses.o: $(MODIFIED_DIR)/neuron/synapses.c $(C_FILES_MODIFIED)
	#synapses.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/spike_processing.o: $(MODIFIED_DIR)/neuron/spike_processing.c $(C_FILES_MODIFIED)
	#spike_processing.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_fixed_impl.o: $(MODIFIED_DIR)/neuron/population_table/population_table_fixed_impl.c $(C_FILES_MODIFIED)
	#population_table/population_table_fixed_impln.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_binary_search_impl.o: $(MODIFIED_DIR)/neuron/population_table/population_table_binary_search_impl.c $(C_FILES_MODIFIED)
	#population_table/population_table_binary_search_impl
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

#STDP Build rules If and only if STDP used
STDP_ENABLED = 0
SYNAPSE_DYNAMICS_O := $(call convert_to_object, $(SYNAPSE_DYNAMICS))
SYNAPTOGENESIS_DYNAMICS_O := $(patsubst $(MODIFIED_DIR)/%.c,$(BUILD_DIR)%.o,$(SYNAPTOGENESIS_DYNAMICS))

ifneq ($(SYNAPSE_DYNAMICS), $(MODIFIED_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c)
    ifdef TIMING_DEPENDENCE_H
	TIMING_DEPENDENCE_H := $(call convert_to_modified, $(TIMING_DEPENDENCE_H))
    else
        $(error TIMING_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS != neuron/plasticity/synapse_dynamics_static_impl.c)
    endif
    ifdef WEIGHT_DEPENDENCE_H
	WEIGHT_DEPENDENCE_H := $(call convert_to_modified, $(WEIGHT_DEPENDENCE_H))
    else
        $(error WEIGHT_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS != neuron/plasticity/synapse_dynamics_static_impl.c)
    endif

    STDP_ENABLED = 1

    STDP_INCLUDES:= -include $(SYNAPSE_TYPE_H) -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H)
    STDP_COMPILE = $(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) $(STDP_INCLUDES)

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS) $(C_FILES_MODIFIED)
	# SYNAPSE_DYNAMICS_O stdp
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(C_FILES_MODIFIED)
	# SYNAPTOGENESIS_DYNAMICS_O stdp
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(BUILD_DIR)neuron/plasticity/common/post_events.o: $(MODIFIED_DIR)/neuron/plasticity/common/post_events.c
	# plasticity/common/post_events.c
	-mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

 else
    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS) $(C_FILES_MODIFIED)
	# $(SYNAPTOGENESIS_DYNAMICS) Synapese
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS) $(C_FILES_MODIFIED)
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

$(BUILD_DIR)neuron/neuron.o: $(MODIFIED_DIR)/neuron/neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H) $(C_FILES_MODIFIED)
	# neuron.o
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      -include $(NEURON_MODEL_H) \
	      -include $(SYNAPSE_TYPE_H) \
	      -include $(INPUT_TYPE_H) \
	      -include $(THRESHOLD_TYPE_H) \
	      -include $(ADDITIONAL_INPUT_H) \
	      -o $@ $<

$(APP_DICT_FILE): $(LOG_DICT_FILES)
	head -2 $(firstword $(LOG_DICT_FILES)) > $(APP_DICT_FILE)
	$(foreach ldf, $(LOG_DICT_FILES), tail -n +3 $(ldf) >> $(APP_DICT_FILE) ;)

# Tidy and cleaning dependencies
clean:
	$(RM) $(OBJECTS) $(APP_OUTPUT_DIR)$(APP).aplx $(APP_DICT_FILE)
	rm -rf $(BUILD_DIR)
	rm -rf $(MODIFIED_DIR)
    # EXTRA_CLEAN_DIRS can be added to but is ignored if empty
	$(foreach ecd, $(EXTRA_CLEAN_DIRS), rm -rf $(ecd);)

.PRECIOUS: $(MODIFIED_DIR)%.c $(MODIFIED_DIR)%.h $(MODIFIED_DICT_FILE) $(EXTRA_PRECIOUS)