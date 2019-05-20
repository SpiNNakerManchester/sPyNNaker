APP = bit_field_expander

#POPULATION_TABLE_IMPL := fixed
POPULATION_TABLE_IMPL := binary_search

SOURCES = bit_field_expander/bit_field_expander.c \
          neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          neuron/direct_synapses.c

include ../neural_support.mk

