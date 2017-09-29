# ---------------------------------------------------------------------
# Sanity checks! Need both SPINN_DIRS and SOURCE_DIR to be set

ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by\
    	running "source setup" in the spinnaker package folder))
endif
ifndef SOURCE_DIR
    $(error SOURCE_DIR is not set.  Please include paths.mk in your main\
    	Makefile.)
endif

# ---------------------------------------------------------------------

ifndef BUILD_DIR
    BUILD_DIR=build/
endif

NEURON_MODEL_O = $(call build_dir, $(NEURON_MODEL))
NEURON_O = $(call build_dir, neuron/neuron.c)
ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE_O = $(call build_dir, $(WEIGHT_DEPENDENCE))
endif
ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE_O = $(call build_dir, $(TIMING_DEPENDENCE))
endif

# ---------------------------------------------------------------------

CFLAGS += -I$(abspath $(BUILD_DIR)) -I$(abspath $(SOURCE_DIR))
CFLAGS += $(patsubst %,-I%,$(subst :, ,$(EXTRA_SRC_DIR)))

SOURCES = \
	common/out_spikes.c \
	neuron/c_main.c \
	neuron/synapses.c \
	neuron/neuron.c \
	neuron/spike_processing.c \
	$(POPULATION_TABLE) \
	$(NEURON_MODEL) \
	$(SYNAPSE_DYNAMICS) \
	$(WEIGHT_DEPENDENCE) \
	$(TIMING_DEPENDENCE) \
	$(OTHER_SOURCES)

# These next three variables are used to set up build rules, but do not
# determine what files are actually required for the build.

SYNAPSE_TYPE_SOURCES += \
    neuron/c_main.c \
    neuron/synapses.c \
    neuron/spike_processing.c \
    neuron/population_table/population_table_fixed_impl.c \
    neuron/population_table/population_table_binary_search_impl.c \
    neuron/plasticity/synapse_dynamics_static_impl.c

STDP += $(wildcard $(SOURCE_DIR)/neuron/plasticity/*/*.c)
STDP += $(wildcard $(SOURCE_DIR)/neuron/plasticity/*/*/*.c)

NEURON_CORE += $(NEURON_MODEL) \
	neuron/neuron.c \
	common/out_spikes.c \
	build/%_build.c

# ---------------------------------------------------------------------

vpath %.h $(SOURCE_DIR):build:$(EXTRA_SOURCE_DIRS)
vpath %.c $(SOURCE_DIR):$(EXTRA_SOURCE_DIRS)
vpath %.tmpl $(SOURCE_DIR)/neuron

include $(SPINN_DIRS)/make/Makefile.SpiNNFrontEndCommon

# No main build rules from upstream makefiles
$(BUILD_DIR)%.o: %.c

# ---------------------------------------------------------------------

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

SYNAPSE_DEP = build/synapse_type.h	   $(SYNAPSE_TYPE_H)
PLASTIC_DEP = build/weight.h		   $(WEIGHT_DEPENDENCE_H) \
			  build/timing.h		   $(TIMING_DEPENDENCE_H)
NEURON_DEP =  build/threshold_type.h   $(THRESHOLD_TYPE_H) \
			  build/neuron_model.h	   $(NEURON_MODEL_H) \
			  build/additional_input.h $(ADDITIONAL_INPUT_H) \
			  build/input_type.h	   $(INPUT_TYPE_H)

# ---------------------------------------------------------------------

define synapse_build_rule
build/$(notdir $(1:.c=.o)): $(1) $(SYNAPSE_DEP)
	@-$$(MKDIR) $$(dir $$@)
	$$(CC) -D__FILENAME__=\"$$(notdir $$<)\" -DLOG_LEVEL=$$(strip $(2)) \
		$$(CFLAGS) -o $$@ $$<
endef

define plasticity_build_rule
build/$(notdir $(1:.c=.o)): $(1) $(SYNAPSE_DEP) $(PLASTIC_DEP)
	@-$$(MKDIR) $$(dir $$@)
	$$(CC) -D__FILENAME__=\"$$(notdir $$<)\" -DLOG_LEVEL=$$(strip $(2)) \
		$$(CFLAGS) -o $$@ $$<
endef

define neuron_build_rule
build/$(notdir $(1:.c=.o)): $(1) $(SYNAPSE_DEP) $(NEURON_DEP)
	@-$$(MKDIR) $$(dir $$@)
	$$(CC) -D__FILENAME__=\"$$(notdir $$<)\" -DLOG_LEVEL=$$(strip $(2)) \
		$$(CFLAGS) -o $$@ $$<
endef

define basic_build_rule
build/$(notdir $(1:.c=.o)): $(1)
	@-$$(MKDIR) $$(dir $$@)
	$$(CC) -D__FILENAME__=\"$$(notdir $$<)\" \
		$$(if $(2), -DLOG_LEVEL=$$(strip $(2))) $$(CFLAGS) -o $$@ $$<
endef

$(foreach file, $(SYNAPSE_TYPE_SOURCES), \
	$(eval $(call synapse_build_rule, $(file), $(SYNAPSE_DEBUG))))
$(foreach file, $(STDP), \
	$(eval $(call plasticity_build_rule, $(file), $(PLASTIC_DEBUG))))
$(foreach file, $(NEURON_CORE), \
	$(eval $(call neuron_build_rule, $(file), $(NEURON_DEBUG))))
$(foreach file, $(OTHER_SOURCES), \
	$(eval $(call basic_build_rule, $(file))))

.PHONY: all clean
