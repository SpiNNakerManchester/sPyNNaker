# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
include $(NEURAL_MODELLING_DIRS)/src/neuron/builds/neural_build.mk
