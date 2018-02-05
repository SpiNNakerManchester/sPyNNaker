# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
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

STDP_RULE_INCLUDE =
ifdef STDP_RULE_H
    STDP_RULE_INCLUDE = -include $$(STDP_RULE_H)
endif

NEURON_O = $(call build_dir, $(SOURCE_DIR)/neuron/neuron.c)

SOURCES = $(SOURCE_DIR)/common/out_spikes.c \
          $(SOURCE_DIR)/neuron/c_main.c \
          $(SOURCE_DIR)/neuron/synapses.c  $(SOURCE_DIR)/neuron/neuron.c \
	      $(SOURCE_DIR)/neuron/spike_processing.c \
	      $(SOURCE_DIR)/neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
	      $(NEURON_MODEL) $(SYNAPSE_DYNAMICS) $(OTHER_SOURCES)

SYNAPSE_TYPE_SOURCES += $(SOURCE_DIR)/neuron/c_main.c \
                        $(SOURCE_DIR)/neuron/synapses.c \
                        $(SOURCE_DIR)/neuron/spike_processing.c \
                        $(SOURCE_DIR)/neuron/population_table/population_table_fixed_impl.c \
                        $(SOURCE_DIR)/neuron/population_table/population_table_binary_search_impl.c \
                        $(SOURCE_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c \
                        $(SOURCE_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl.c

include $(SPINN_DIRS)/make/Makefile.SpiNNFrontEndCommon

define synapse_type_rule
$$(call build_dir, $(1)): $(1) $$(SYNAPSE_TYPE_H)
	-mkdir -p $$(dir $$@)
	$$(CC) -D__FILE__=\"$$(notdir $$*.c)\" -DLOG_LEVEL=$(SYNAPSE_DEBUG) \
	        $$(CFLAGS) \
	        -include $$(SYNAPSE_TYPE_H) $(STDP_RULE_INCLUDE) -o $$@ $$<
endef

$(foreach obj, $(SYNAPSE_TYPE_SOURCES), $(eval $(call synapse_type_rule, $(obj))))

$(NEURON_MODEL_O): $(NEURON_MODEL)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(NEURON_DEBUG) \
	        $(CFLAGS) -o $@ $<

$(NEURON_O): $(SOURCE_DIR)/neuron/neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"neuron.c\" -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      -include $(NEURON_MODEL_H) \
	      -include $(SYNAPSE_TYPE_H) \
	      -include $(INPUT_TYPE_H) \
	      -include $(THRESHOLD_TYPE_H) \
	      -include $(ADDITIONAL_INPUT_H) -o $@ $<
