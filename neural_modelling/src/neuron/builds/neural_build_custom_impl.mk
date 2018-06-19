# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif

ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    NEURON_DEBUG = LOG_DEBUG
    PLASTIC_DEBUG = LOG_DEBUG
endif

ifndef NEURON_DEBUG
    NEURON_DEBUG = LOG_INFO
endif

ifndef PLASTIC_DEBUG
    PLASTIC_DEBUG = LOG_INFO
endif

#POPULATION_TABLE_IMPL := fixed
POPULATION_TABLE_IMPL := binary_search

ifndef NEURON_IMPL_H
    $(error NEURON_IMPL_H is not set.  Please select a neuron implementation)
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

ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS = $(SOURCE_DIR)/neuron/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNGEN_ENABLED = 0
endif

NEURON_O = $(call build_dir, $(SOURCE_DIR)/neuron/neuron.c)

SOURCES = $(SOURCE_DIR)/common/out_spikes.c \
          $(SOURCE_DIR)/neuron/c_main.c \
          $(SOURCE_DIR)/neuron/synapses.c  $(SOURCE_DIR)/neuron/neuron.c \
	      $(SOURCE_DIR)/neuron/spike_processing.c \
	      $(SOURCE_DIR)/neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
	      $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) \
	      $(TIMING_DEPENDENCE) $(OTHER_SOURCES) $(SYNAPTOGENESIS_DYNAMICS)

STDP_ENABLED = 0
ifneq ($(SYNAPSE_DYNAMICS), $(SOURCE_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c)
    STDP += $(SYNAPSE_DYNAMICS) \
            $(SOURCE_DIR)/neuron/plasticity/common/post_events.c \
            $(SYNAPTOGENESIS_DYNAMICS)
    STDP_ENABLED = 1
endif

include $(SPINN_DIRS)/make/FrontEndCommon.mk
FEC_OPT = $(OSPACE)
CFLAGS += -I$(NEURAL_MODELLING_DIRS)/src

define stdp_rule
$$(call build_dir, $(1)): $(1) $$(SYNAPSE_TYPE_H) \
                               $$(WEIGHT_DEPENDENCE_H) $$(TIMING_DEPENDENCE_H)
	-mkdir -p $$(dir $$@)
	$$(CC) -D__FILE__=\"$$(notdir $$*.c)\" -DLOG_LEVEL=$$(PLASTIC_DEBUG) \
	      $$(CFLAGS) \
	      -DSTDP_ENABLED=$(STDP_ENABLED) \
	      -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) \
	      -include $$(SYNAPSE_TYPE_H) \
	      -include $$(WEIGHT_DEPENDENCE_H) \
	      -include $$(TIMING_DEPENDENCE_H) -o $$@ $$<
endef

$(foreach obj, $(STDP), $(eval $(call stdp_rule, $(obj))))

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE) $(SYNAPSE_TYPE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"$(notdir $*.c)\" -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H)\
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(NEURON_O): $(SOURCE_DIR)/neuron/neuron.c $(NEURON_MODEL_H) \
                             $(SYNAPSE_TYPE_H)
	-mkdir -p $(dir $@)
	$(CC) -D__FILE__=\"neuron.c\" -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) \
	      -include $(NEURON_IMPL_H) -o $@ $<
