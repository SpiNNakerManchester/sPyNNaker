APP = $(notdir $(CURDIR))$(EXT)
SOURCE_DIR = $(NEURAL_MODELLING_DIRS)/src/neuron
MODEL_OBJS = $(SOURCE_DIR)/models/lif_cond.o $(SOURCE_DIR)/plasticity/common/post_events.o $(SOURCE_DIR)/plasticity/stdp/stdp_mad.o $(SOURCE_DIR)/plasticity/common/maths.o $(SOURCE_DIR)/plasticity/stdp/timing_dependence/pair.o $(SOURCE_DIR)/plasticity/stdp/weight_dependence/additive_one_term.o
NEURON_MODEL_H = ../../models/lif_cond.h
SYNAPSE_SHAPING_H = ../../synapses/exponential_impl.h
STDP_TYPEDEFS_H = ../../plasticity/stdp/stdp_typedefs.h
TIMING_DEPENDENCE_H = ../../plasticity/stdp/timing_dependence/pair_impl.h
WEIGHT_DEPENDENCE_H = ../../plasticity/stdp/weight_dependence/additive_one_term_impl.h

include ../Makefile.common

$(BUILDDIR)/neuron/plasticity/stdp/timing_dependence/pair.o: $(SOURCE_DIR)/plasticity/stdp/timing_dependence/pair.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(SYNAPSE_SHAPING_H) -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/stdp/weight_dependence/additive_one_term.o: $(SOURCE_DIR)/plasticity/stdp/weight_dependence/additive_one_term.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(SYNAPSE_SHAPING_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/stdp/stdp_mad.o: $(SOURCE_DIR)/plasticity/stdp/stdp_mad.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(SYNAPSE_SHAPING_H) -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/common/post_events.o: $(SOURCE_DIR)/plasticity/common/post_events.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(SYNAPSE_SHAPING_H)  -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H) -o $@ $<