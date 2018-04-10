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

ifndef ADDITIONAL_INPUT_H
    ADDITIONAL_INPUT_H = $(SOURCE_DIR)/neuron/additional_inputs/additional_input_none_impl.h
endif

ifndef NEURON_MODEL
    $(error NEURON_MODEL is not set.  Please choose a neuron model to compile)
else
    NEURON_MODEL_O = $(call build_dir, $(NEURON_MODEL))
endif

ifndef NEURON_MODEL_H
    $(error NEURON_MODEL_H is not set.  Please select a neuron model header file)
endif

ifndef INPUT_TYPE_H
    $(error INPUT_TYPE_H is not set.  Please select an input type header file)
endif

ifndef THRESHOLD_TYPE_H
    $(error THRESHOLD_TYPE_H is not set.  Please select a threshold type header file)
endif

ifndef SYNAPSE_TYPE_H
    $(error SYNAPSE_TYPE_H is not set.  Please select a synapse type header file)
endif

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
endif

ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE_O = $(call build_dir, $(WEIGHT_DEPENDENCE))
endif

ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE_O = $(call build_dir, $(TIMING_DEPENDENCE))
endif

SYNGEN_ENABLED = 1

ifndef SYNAPTOGENESIS_DYNAMICS_H
    SYNAPTOGENESIS_DYNAMICS_H = $(SOURCE_DIR)/neuron/synaptogenesis_dynamics.h
    SYNGEN_ENABLED = 0
endif

ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS = $(SOURCE_DIR)/neuron/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNGEN_ENABLED = 0
endif

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(dir $(MAKEFILE_PATH))
SOURCE_DIR := $(abspath $(CURRENT_DIR))
SOURCE_DIRS += $(SOURCE_DIR)
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(CURRENT_DIR)../../spynnaker/pyNN/model_binaries/)/
endif


all: $(APP_OUTPUT_DIR)$(APP).aplx $(COPIED_DIRS)

include $(NEURAL_MODELLING_DIRS)/commoncopy.mk
COPIED_DIRS += $(COMMON_MODIFIED_DIR)

include $(NEURAL_MODELLING_DIRS)/neuroncopy.mk
COPIED_DIRS += $(NEURON_MODIFIED_DIR)

NEURON_O = $(call build_dir, $(SOURCE_DIR)/neuron/neuron.c)

SOURCES = $(SOURCE_DIR)/common/out_spikes.c \
          $(SOURCE_DIR)/neuron/c_main.c \
          $(SOURCE_DIR)/neuron/synapses.c  $(SOURCE_DIR)/neuron/neuron.c \
	      $(SOURCE_DIR)/neuron/spike_processing.c \
	      $(SOURCE_DIR)/neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
	      $(NEURON_MODEL) $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) \
	      $(TIMING_DEPENDENCE) $(OTHER_SOURCES) $(SYNAPTOGENESIS_DYNAMICS)

SYNAPSE_TYPE_SOURCES += $(SOURCE_DIR)/neuron/c_main.c \
                        $(SOURCE_DIR)/neuron/synapses.c \
                        $(SOURCE_DIR)/neuron/spike_processing.c \
                        $(SOURCE_DIR)/neuron/population_table/population_table_fixed_impl.c \
                        $(SOURCE_DIR)/neuron/population_table/population_table_binary_search_impl.c \
                        $(SOURCE_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c \
                        $(SYNAPTOGENESIS_DYNAMICS)

STDP_ENABLED = 0
ifneq ($(SYNAPSE_DYNAMICS), $(SOURCE_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c)
    STDP += $(SYNAPSE_DYNAMICS) \
            $(SOURCE_DIR)/neuron/plasticity/common/post_events.c \
            $(SYNAPTOGENESIS_DYNAMICS)
    STDP_ENABLED = 1
endif

ifndef SOURCE_DIRS
    $(error SOURCE_DIRS is not set.  Please define SOURCE_DIRS)
endif

ifndef APP_OUTPUT_DIR
    $(error APP_OUTPUT_DIR is not set.  Please define APP_OUTPUT_DIR)
endif

ifndef BUILD_DIR
    $(error BUILD_DIR is not set.  Please define BUILD_DIR)
endif


define define-build-code
$$(BUILD_DIR)%.o: $1/%.c
	-mkdir -p $$(dir $$@)
	$$(CC) $$(CFLAGS) -D__FILENAME__=\"$$(notdir $$*.c)\" -o $$@ $$<
endef

define source_dir
$(firstword $(abspath $(strip $(foreach dir, $(sort $(SOURCE_DIRS)), $(findstring $(dir), $(1))))))
endef

define build_dir
$(patsubst $(call source_dir, $(1))/%.c,$(BUILD_DIR)%.o,$(1))
endef

# Convert the objs into the correct format to work here
OBJS := $(abspath $(SOURCES))
$(foreach dir, $(sort $(SOURCE_DIRS)), $(eval OBJS := $(OBJS:$(abspath $(dir))/%.c=$(BUILD_DIR)%.o)))
$(foreach dir, $(sort $(SOURCE_DIRS)), $(eval $(call define-build-code,$(dir))))
OBJECTS += $(OBJS)

LIBRARIES += -lspinn_frontend_common -lspinn_common -lm
FEC_DEBUG := PRODUCTION_CODE
PROFILER := PROFILER_DISABLED

# Run md5sum on application name and extract first 8 bytes
SHELL = bash
APPLICATION_NAME_HASH = $(shell echo -n "$(APP)" | (md5sum 2>/dev/null || md5) | cut -c 1-8)

CFLAGS += -Wall -Wextra -D$(FEC_DEBUG) -D$(PROFILER) $(OTIME) -DAPPLICATION_NAME_HASH=0x$(APPLICATION_NAME_HASH)

include $(SPINN_DIRS)/make/Makefile.common

# Tidy and cleaning dependencies
clean:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt $(APP_OUTPUT_DIR)$(APP).aplx

CFLAGS += -I $(COMMON_MODIFIED_DIR)

INCLUDE_NEURON_HEADERS = -I $(NEURAL_MODELLING_DIRS)/src/neuron
INCLUDE_PLASTICITY_HEADERS = $(INCLUDE_NEURON_HEADERS) -I $(NEURAL_MODELLING_DIRS)/src/neuron/plasticity

define synapse_type_rule
$$(call build_dir, $(1)): $(1) $$(SYNAPSE_TYPE_H)
	-mkdir -p $$(dir $$@)
	$$(CC) -D__FILE__=\"$$(notdir $$*.c)\" -DLOG_LEVEL=$(SYNAPSE_DEBUG) \
	        $$(CFLAGS) $(INCLUDE_PLASTICITY_HEADERS) \
	        -DSTDP_ENABLED=$(STDP_ENABLED) \
	        -include $(SYNAPSE_TYPE_H) -o $$@ $$<
endef

define stdp_rule
$$(call build_dir, $(1)): $(1) $$(SYNAPSE_TYPE_H) \
                               $$(WEIGHT_DEPENDENCE_H) $$(TIMING_DEPENDENCE_H)
	-mkdir -p $$(dir $$@)
	$$(CC) -D__FILE__=\"$$(notdir $$*.c)\" -DLOG_LEVEL=$$(PLASTIC_DEBUG) \
	      $$(CFLAGS) $(INCLUDE_PLASTICITY_HEADERS) \
	      -DSTDP_ENABLED=$(STDP_ENABLED) \
	      -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) \
	      -include $$(SYNAPSE_TYPE_H) \
	      -include $$(WEIGHT_DEPENDENCE_H) \
	      -include $$(TIMING_DEPENDENCE_H) -o $$@ $$<
endef

$(foreach obj, $(SYNAPSE_TYPE_SOURCES), $(eval $(call synapse_type_rule, $(obj))))
$(foreach obj, $(STDP), $(eval $(call stdp_rule, $(obj))))

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE) $(SYNAPSE_TYPE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        $(INCLUDE_PLASTICITY_HEADERS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        $(INCLUDE_PLASTICITY_HEADERS) \
	        -include $(SYNAPSE_TYPE_H)\
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(NEURON_MODEL_O): $(NEURON_MODEL)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(NEURON_DEBUG) \
	        $(CFLAGS) -o $@ $<

$(NEURON_O): $(SOURCE_DIR)/neuron/neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"neuron.c\" -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      $(INCLUDE_NEURON_HEADERS) \
	      -include $(NEURON_MODEL_H) \
	      -include $(SYNAPSE_TYPE_H) \
	      -include $(INPUT_TYPE_H) \
	      -include $(THRESHOLD_TYPE_H) \
	      -include $(ADDITIONAL_INPUT_H) \
	      -include $(SYNAPTOGENESIS_DYNAMICS_H) -o $@ $<
