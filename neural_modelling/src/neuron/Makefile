MODELS = IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         IF_curr_exp_stdp_pair_additive \
         IF_curr_exp_stdp_pair_multiplicative \
         IF_curr_exp_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_pair_multiplicative \
         IF_cond_exp_stdp_mad_pair_additive
BUILD_DIRS := $(addprefix builds/, $(MODELS))

all:
	@for d in $(BUILD_DIRS); do $(MAKE) -C $$d all || exit $$?; done

clean:
	@for d in $(BUILD_DIRS); do $(MAKE) -C $$d clean || exit $$?; done

.PHONY: all clean
