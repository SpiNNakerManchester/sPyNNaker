APP = $(notdir $(CURDIR))$(EXT)
MODEL_OBJS = ../../models/lif_curr.o ../../plasticity/common/post_events.o ../../plasticity/stdp/stdp.o ../../plasticity/common/maths.o ../../plasticity/stdp/timing_dependence/pair.o ../../plasticity/stdp/weight_dependence/additive.o
NEURON_MODEL_H = ../../models/lif_curr.h
SYNAPSE_SHAPING_H = ../../synapses/exponential_impl.h
STDP_TYPEDEFS_H = ../../plasticity/stdp/stdp_typedefs.h
TIMING_DEPENDENCE_H = ../../plasticity/stdp/timing_dependence/pair_impl.h
WEIGHT_DEPENDENCE_H = ../../plasticity/stdp/weight_dependence/additive_fast_impl.h

include ../Makefile.common

$(BUILDDIR)/neuron/plasticity/stdp/timing_dependence/pair.o: ../../plasticity/stdp/timing_dependence/pair.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/stdp/stdp.o: ../../plasticity/stdp/stdp.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(WEIGHT_DEPENDENCE_H) -include $(SYNAPSE_SHAPING_H) -include $(TIMING_DEPENDENCE_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/common/post_events.o: ../../plasticity/common/post_events.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TYPEDEFS_H) -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H) -o $@ $<