APP = $(notdir $(CURDIR))$(EXT)
MODEL_OBJS = ../../models/lif_curr.o ../../plasticity/stdp_trace.o ../../plasticity/stdp_trace_pair.o ../../plasticity/events.o ../../plasticity/maths.o
NEURON_MODEL_H = ../../models/lif_curr.h
SYNAPSE_SHAPING_H = ../../synapses/exponential_impl.h
STDP_TRACE_RULE_H = ../../plasticity/stdp_trace_pair_impl.h


include ../Makefile.common

$(BUILDDIR)/neuron/plasticity/stdp_trace.o: ../../plasticity/stdp_trace.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TRACE_RULE_H) -include $(SYNAPSE_SHAPING_H) -o $@ $<

$(BUILDDIR)/neuron/plasticity/events.o: ../../plasticity/events.c
	-mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -include $(STDP_TRACE_RULE_H) -o $@ $<