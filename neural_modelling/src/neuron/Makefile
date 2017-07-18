MODELS = IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         IF_curr_exp_stdp_pair_additive \
         IF_curr_exp_stdp_pair_multiplicative \
         IF_curr_exp_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_pair_multiplicative \
         IF_cond_exp_stdp_mad_pair_additive \
         external_device_lif_control
BUILD_DIRS := $(addprefix builds/, $(MODELS))

all: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

clean: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
