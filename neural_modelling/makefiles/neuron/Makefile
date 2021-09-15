MODELS = IF_cond_comb_exp_2E2I_stdp_mad_cyclic_cyclic\
         IF_cond_comb_exp_2E2I
         #IF_cond_exp_2E2I_stdp_mad_cyclic_cyclic \
         #IF_cond_exp_2E2I \
         #IF_curr_comb_exp_2E2I_stdp_mad_cyclic_cyclic\    
         #IF_curr_comb_exp_2E2I \ 
         #IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         IF_curr_exp_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_pair_multiplicative \
         IF_cond_exp_stdp_mad_pair_additive \
         external_device_lif_control \
         IF_cond_exp_stoc \
         IF_curr_exp_stdp_mad_recurrent_pre_stochastic_multiplicative \
         IF_curr_exp_stdp_mad_recurrent_dual_fsm_multiplicative \
         IF_curr_exp_stdp_mad_vogels_2011_additive \
         IF_curr_delta \
         IF_curr_exp_ca2_adaptive \
         IF_curr_exp_ca2_adaptive_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_nearest_pair_additive \
         IF_curr_exp_stdp_mad_nearest_pair_multiplicative \
         IF_curr_exp_stdp_mad_pfister_triplet_additive \
         IF_cond_exp_stdp_mad_nearest_pair_additive \
	     IF_curr_alpha \
	     IF_curr_alpha_stdp_mad_pair_additive \
         IF_cond_exp_structural \
         IF_curr_exp_stdp_mad_pair_additive_structural \
         IF_curr_exp_structural \
         IF_cond_exp_stdp_mad_pair_additive_structural \
         IF_curr_exp_sEMD

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done
