MODELS = IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         external_device_lif_control \
         IF_cond_exp_stoc \
         IF_curr_delta \
         IF_curr_exp_ca2_adaptive \
	     IF_curr_alpha \
         IF_cond_exp_structural \
         IF_curr_exp_structural \
         IF_curr_comb_exp_2E2I \
         IF_curr_comb_exp_2E2I_stdp_mad_cyclic_cyclic \
         
BUILD_DIRS := $(addprefix builds/, $(MODELS))

all: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do $(MAKE) -C $$d || exit $$?; done

clean: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do $(MAKE) -C $$d clean || exit $$?; done
