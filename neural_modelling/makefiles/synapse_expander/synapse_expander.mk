APP = synapse_expander
BUILD_DIR = build/
SOURCES = synapse_expander/rng.c \
          synapse_expander/param_generator.c \
          synapse_expander/connection_generator.c \
          synapse_expander/matrix_generator.c \
          synapse_expander/synapse_expander.c

include ../neural_support.mk
