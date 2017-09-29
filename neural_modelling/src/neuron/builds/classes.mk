# ---------------------------------------------------------------------

ifndef NEURON_MODEL
    $(error NEURON_MODEL is not set.  Please choose a neuron model to compile)
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
ifneq ($(notdir $(SYNAPSE_DYNAMICS)),synapse_dynamics_static_impl.c)
    ifndef TIMING_DEPENDENCE
        $(warning SYNAPSE_DYNAMICS set to non-static rule but TIMING_DEPENDENCE unset)
    endif
    ifndef WEIGHT_DEPENDENCE
        $(warning SYNAPSE_DYNAMICS set to non-static rule but WEIGHT_DEPENDENCE unset)
    endif
endif

#POPULATION_TABLE_TYPE := fixed
POPULATION_TABLE_TYPE := binary_search

POPULATION_TABLE = neuron/population_table/population_table_$(POPULATION_TABLE_TYPE)_impl.c

ifndef ADDITIONAL_INPUT_H
    ADDITIONAL_INPUT_H = neuron/additional_inputs/additional_input_none_impl.h
endif

# ---------------------------------------------------------------------
# Convert the filenames for interface implementations into actual
# includeable files.
# ---------------------------------------------------------------------

REPLACER=python $(abspath $(SOURCE_DIR)/../utils/replace.py)
define template_rule
build/$$(notdir $(1)).h: $(1).tmpl Makefile
	@-$$(MKDIR) $$(dir $$@)
	@echo replace $(2) in $(1).tmpl making $$@
	@$$(REPLACER) $(2) $$($(2)) $$< $$@
endef

$(eval $(call template_rule,additional_inputs/additional_input,ADDITIONAL_INPUT_H))
$(eval $(call template_rule,input_types/input_type,INPUT_TYPE_H))
$(eval $(call template_rule,models/neuron_model,NEURON_MODEL_H))
$(eval $(call template_rule,synapse_types/synapse_type,SYNAPSE_TYPE_H))
$(eval $(call template_rule,threshold_types/threshold_type,THRESHOLD_TYPE_H))
$(eval $(call template_rule,plasticity/stdp/timing_dependence/timing,TIMING_DEPENDENCE_H))
$(eval $(call template_rule,plasticity/stdp/weight_dependence/weight,WEIGHT_DEPENDENCE_H))
