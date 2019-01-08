APP = $(notdir $(CURDIR))

NEURON_MODEL = $(NEURON_DIR)/neuron/models/neuron_model_lif_impl.c
NEURON_MODEL_H = $(NEURON_DIR)/neuron/models/neuron_model_lif_impl.h
INPUT_TYPE_H = $(NEURON_DIR)/neuron/input_types/input_type_conductance.h
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_standard.h
THRESHOLD_TYPE_H = $(NEURON_DIR)/neuron/threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = $(NEURON_DIR)/neuron/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c
SYNAPTOGENESIS_DYNAMICS = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/topographic_map_impl.c
PARTNER_SELECTION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/last_neuron_selection_impl.c
PARTNER_SELECTION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/last_neuron_selection_impl.h

include ../neural_build.mk