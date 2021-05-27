<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<tagfile doxygen_version="1.9.1">
  <compound kind="file">
    <name>bit_field_expander.c</name>
    <path>/github/workspace/neural_modelling/src/bit_field_expander/</path>
    <filename>bit__field__expander_8c.html</filename>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <includes id="direct__synapses_8h" name="direct_synapses.h" local="no" imported="no">neuron/direct_synapses.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="no" imported="no">neuron/population_table/population_table.h</includes>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" imported="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <class kind="struct">builder_region_struct</class>
    <member kind="define">
      <type>#define</type>
      <name>BYTE_TO_WORD_CONVERSION</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>ac9b2b86329da8040e6c2257d65b0a251</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>N_NEURONS</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a06f93843e9bcfa4f58d70e41333ce0af</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>N_SYNAPSE_TYPES</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>aed4ffe162776a6c89746019dda4d592f</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static vcpu_t *</type>
      <name>vcpu</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a3f6a8a68b4b17ff5dfc9625fcbca0ba5</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>fail_shut_down</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>acbb8b3b888337366c49aa83e72172383</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>success_shut_down</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a1218cee1aa99ae955d38901097ba2eea</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>read_in_addresses</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a4a87539383a9998fa1063e982f63e0a3</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>initialise</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a08e046aae605f0fc1ba5dc96b1d2f09a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>process_synaptic_row</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a138926c3ded07524f2b617eb4ba8b96b</anchor>
      <arglist>(synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>do_sdram_read_and_test</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a5eadce86b92d6e5f04e21e7532745ade</anchor>
      <arglist>(synaptic_row_t row, uint32_t n_bytes_to_transfer)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>sort_by_key</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>af9ca4dbc2f71c68e5140742c020f8380</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>determine_redundancy</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a73a98b51cca3f71b0eee0817f2d6eab8</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>generate_bit_field</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a05cd52c8292c3bab8005816a1b7d5645</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>FAILED_REGION_ID</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a9132a44b6d09c3f7ffd226f8e16f11a9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>address_t</type>
      <name>master_pop_base_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>ae5b6bc86a4a4b0a6873f106ef9082005</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>address_t</type>
      <name>synaptic_matrix_base_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>aa848568a69120df24c0430e5ee983c5c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>filter_region_t *</type>
      <name>bit_field_base_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a445fa555a051ef68edc27fc90a89ec65</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>address_t</type>
      <name>direct_matrix_region_base_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>aa1da3d4b23e323da04f859a8d9eb6c69</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>address_t</type>
      <name>structural_matrix_region_base_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a37444ff66ef05a9fff67975a7b9a3427</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>address_t</type>
      <name>direct_synapses_address</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a7e8f73474622d82215423413dec84223</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>row_max_n_words</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>af9b6824a750777e79471f086307d51b9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>key_atom_data_t *</type>
      <name>keys_to_max_atoms</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>ace2af7f42ceddbe32acd8a8e32c9aa4e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_keys_to_max_atom_map</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a10c000a085edd682afcaf53023749648</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_vertex_regions</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>aecf3dda26a0c94057f7ff47a66de4e68</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bit_field_t *</type>
      <name>fake_bit_fields</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>abab455406701d8b67a962835f9175899</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>synaptic_row_t</type>
      <name>row_data</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a7a0a788410818524ea425e5287922f92</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bool</type>
      <name>can_run</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a08d5046cd90ed4bcb3d31721e5fa3452</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rewiring_data_t</type>
      <name>rewiring_data</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a14052fb746b24752fc5a96accf39d8b8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static post_to_pre_entry *</type>
      <name>post_to_pre_table</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>ab4adc13b137ccdbaff9d8883400182eb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>pre_pop_info_table_t</type>
      <name>pre_info</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a25e63ee99aecac3677f299c1cccec889</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>in_spikes.h</name>
    <path>/github/workspace/neural_modelling/src/common/</path>
    <filename>in__spikes_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="yes" imported="no">neuron-typedefs.h</includes>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>in_spikes_initialize_spike_buffer</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a9cc56cd2e4bbe79b5a722357f1959185</anchor>
      <arglist>(uint32_t size)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>in_spikes_add_spike</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>af50c3c392fbfb0d59e24eb90eb06e9f4</anchor>
      <arglist>(spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>in_spikes_get_next_spike</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a27d508007a6c99c3d80caed473318b08</anchor>
      <arglist>(spike_t *spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>in_spikes_is_next_spike_equal</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a2ae3e298f1e13b8804dc826a229c6669</anchor>
      <arglist>(spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static counter_t</type>
      <name>in_spikes_get_n_buffer_overflows</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>ae405867606c4cf942b7507b9ca5baf4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static counter_t</type>
      <name>in_spikes_get_n_buffer_underflows</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>ae98f5c1851e73d640276add2c7793df1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>in_spikes_print_buffer</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>af2c8052da82bc8ce24310a278994ef33</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>in_spikes_input_index</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a7437cf899a2be1ed04cb5cd2c445051d</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>in_spikes_output_index</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a06eb057099ca98c17d7aca3cf1754636</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>in_spikes_real_size</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a4fdfc400d8b3a5f4456b56de6e1b42a1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>in_spikes_size</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>ad5a175358e725bd447fc7cb91124c30e</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>in_spikes_clear</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>ac887c7341817b49b9ce0ecb9a0fa479c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static spike_t</type>
      <name>in_spikes_value_at_index</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a645f3cede41ec753b8d9cae272b37dda</anchor>
      <arglist>(uint32_t index)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static circular_buffer</type>
      <name>buffer</name>
      <anchorfile>in__spikes_8h.html</anchorfile>
      <anchor>a82b41c0e86ad17367ee541feb04c22f9</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>maths-util.h</name>
    <path>/github/workspace/neural_modelling/src/common/</path>
    <filename>maths-util_8h.html</filename>
    <member kind="define">
      <type>#define</type>
      <name>START</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a3018c7600b7bb9866400596a56a57af7</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>REAL_CONST</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a0ac3b00bb3dbd6b05a21cb12708b8f8d</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>UREAL_CONST</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a9ff1e35d7d395a988bf688a412076a40</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>FRACT_CONST</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ade056d60ae7bac69fab1196cc114cfb3</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>UFRACT_CONST</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a6c28d1472e31da898fa9a584c9e82d01</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>ONE</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a206b6f5362e56b51ca957635350b70b6</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>HALF</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a37c4c48ff47f0838f64b5a1fb3c803b2</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>ZERO</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ac328e551bde3d39b6d7b8cc9e048d941</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>ACS_DBL_TINY</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a384a1b0ced36846fd8efb19c26c29a35</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SQRT</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ae52c48592a33f8f3db9592f7be0502f3</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>EXP</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a179978530f93b1e13bc48dc40dc1960e</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>ABS</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a996f7be338ccb40d1a2a5abc1ad61759</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SIGN</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a1088484ff7d8b0a6809c495f99580f50</anchor>
      <arglist>(x, y)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>REAL_COMPARE</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a312d47ef9413a82783b9a70de764d9a2</anchor>
      <arglist>(x, op, y)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>REAL_TWICE</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ac5b558ffc8e6ef1ff9e8703ad39abfb4</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>REAL_HALF</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>acb3ba35e71e4ec24a52b48d53308d3c2</anchor>
      <arglist>(x)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MIN_HR</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a6daffdd851dffa46c5be64d52af96db8</anchor>
      <arglist>(a, b)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MAX_HR</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a4cd8c0908147af30685131571083c3f1</anchor>
      <arglist>(a, b)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SQR</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ad41630f833e920c1ffa34722f45a8e77</anchor>
      <arglist>(a)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CUBE</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a3e97109573f7a38ddc9e9c1a9dbb6758</anchor>
      <arglist>(a)</arglist>
    </member>
    <member kind="typedef">
      <type>unsigned int</type>
      <name>Card</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a63fe77b0ec710597cb0b69eee8d90aaf</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>accum</type>
      <name>REAL</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a67277c5a9b43a598ef8c22aea7dbe1b6</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>unsigned accum</type>
      <name>UREAL</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a2e4c6b7f842497114d81356c763536c4</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>long fract</type>
      <name>FRACT</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a1b5bb55fc4fc8f2e3a5b377aa6ab36ba</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>unsigned long fract</type>
      <name>UFRACT</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a8cf409d4308be505fbdb5683525213ba</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>munich_protocol.h</name>
    <path>/github/workspace/neural_modelling/src/common/</path>
    <filename>munich__protocol_8h.html</filename>
    <class kind="struct">munich_key_bitfields_t</class>
    <class kind="union">munich_key_t</class>
    <class kind="struct">multicast_packet</class>
    <member kind="define">
      <type>#define</type>
      <name>MUNICH_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a8200ce065b6bf4ef334ad1b33451bf96</anchor>
      <arglist>(I, F, D)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MUNICH_KEY_I_D</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a5dafb96b044783c3b4650c5789f6f08a</anchor>
      <arglist>(I, D)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MUNICH_KEY_I</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ac9ffc4cc9a38bac6bb565c793d90ec81</anchor>
      <arglist>(I)</arglist>
    </member>
    <member kind="enumvalue">
      <name>OFFSET_TO_I</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a06fc87d81c62e9abb8790b6e5713c55baa890a0ce75c6dee9ecbac3a2c87220cc</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>OFFSET_TO_F</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a06fc87d81c62e9abb8790b6e5713c55ba964ef105cedcef1b651c6a4e58e33302</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>OFFSET_TO_D</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a06fc87d81c62e9abb8790b6e5713c55baad87c155efc7814564f9b47dfb651b3f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>OFFSET_FOR_UART_ID</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adf764cbdea00d65edcd07bb9953ad2b7ae6c8af4026bd86e948aaf189d1c04e91</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adf764cbdea00d65edcd07bb9953ad2b7a3194db92087aedb945479152ff1dabe1</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_OFFSET_FOR_TIMESTAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a99fb83031ce9923c84392b4e92f956b5afc03d8a1fbea6053f8d14e704cca9462</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_OFFSET_FOR_RETINA_SIZE</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a99fb83031ce9923c84392b4e92f956b5abc9f9dd3f1a2cac8b0a2d6eda2bcc3e5</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_SENSOR_ID_OFFSET</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a99fb83031ce9923c84392b4e92f956b5a6ad12602c70c04f6da611cc36d9822fb</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_OFFSET_FOR_SENSOR_TIME</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a99fb83031ce9923c84392b4e92f956b5afe00a4850a038af3dc4ed6d35575a572</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CONFIGURE_MASTER_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a635089693fa56b24e14b697b004fc204</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CHANGE_MODE</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a4984f59c2d1880d5dd6b2f81c3bd932b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DISABLE_RETINA_EVENT_STREAMING</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a5cc988b8c6e1e4b586915036edcd57f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a94eba6b9c22bf274e6ff81d58c229afd</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ACTIVE_RETINA_EVENT_STREAMING_SET_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a6aec4d5e40d24d80269f24f186e12ce0</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SET_TIMER_COUNTER_FOR_TIMESTAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a74cd8f0dde766e3c78118ca85fd4f20e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MASTER_SLAVE_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04acebd4bfb16f8f5acfc2234d9f65207c8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BIAS_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a86e8b86d0f722dc54808c12fc3d5d4e2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>RESET_RETINA_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aac54162f9b613c9ea627ae35225021d2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SENSOR_REPORTING_OFF_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04abcc37f6aec28a96a4f0482cdd52db61e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>POLL_SENSORS_ONCE_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04af411423d32b0d5b899c3ac16f6d616f7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>POLL_SENSORS_CONTINUOUSLY_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04ac78ecb26d0149528ab6d114d5a2a7d2d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DISABLE_MOTOR_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aa50cb29eaf9f334bf5a204d2d52ae66e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_RUN_FOR_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a21103f8167edea1b62a71b6d6dc1f093</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_0_RAW_PERM_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a687b06affd6532e895d0bc8dc00095be</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_1_RAW_PERM_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04acc148fefb0b2e5151ceb48f46ecbee40</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_0_RAW_LEAK_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a914825da898d58ae3921f3d69dae630c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_1_RAW_LEAK_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a300052c8eb8452f20d4350e94ca1bb62</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_A_TOTAL_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aec9017d18ebca73b7369bc5613c1b5c4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_B_TOTAL_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a3cd79f1f3855fc1706b48ca71d857805</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_C_TOTAL_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a4f3cca726da9976ac97b02a6b4a1a5a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_A_CHANNEL_0_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a3efc64a9972b3a6e10d2bacb2b0d7560</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_A_CHANNEL_1_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a1cdc823f8771ea1e77af9f4f201ff996</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_B_CHANNEL_0_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04afd31f812c1b600519d81a73247a1176b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_B_CHANNEL_1_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a80d9d4abcabdb99bf246331a0faa6dea</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_C_CHANNEL_0_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a3eda075963d5dd6ad7ae6b409716a78b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTOR_TIMER_C_CHANNEL_1_ACTIVE_PERIOD_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a0563d2e2bcf2832190ca0b2e1e8436f8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>QUERY_STATES_LINES_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aeff0972ddb0907acd404528f8f246a48</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SET_OUTPUT_PATTERN_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04ab50c8ed18766cbc286dc692db6a44cc4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ADD_PAYLOAD_TO_CURRENT_OUTPUT_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04af715c89e8a41d4dda0acbd050c6cd962</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>REMOVE_PAYLOAD_TO_CURRENT_OUTPUT_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a1e4713ab52d9efee9beaa14486b59ea4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SET_PAYLOAD_TO_HIGH_IMPEDANCE_KEY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04af9f1c8e048e0297a7d9b02686fd001b4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LASER_CONFIG_TOTAL_PERIOD</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a92aa458811e2d91fa2a2ddc7c6300c08</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LASER_CONFIG_ACTIVE_TIME</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aaf64f130ca2b0371a27d61e97ee5dfca</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LASER_FREQUENCY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a667772b48cfbd160decaa2e2d59070db</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LED_CONFIG_TOTAL_PERIOD</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04aabd5c2fe1fdf4dbe9591b4bde8912ffe</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LED_BACK_CONFIG_ACTIVE_TIME</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a5b8710ac916aa67a3c2a64837e6b7720</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LED_FRONT_CONFIG_ACTIVE_TIME</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a969de1a1796dd1b7b8664800ab665fd6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_LED_FREQUENCY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a95841ef9e558fd3a052b371cd2ba2ce4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_SPEAKER_CONFIG_TOTAL_PERIOD</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04ae0391bb2f6e1b09e79d782783f7d27ed</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_SPEAKER_CONFIG_ACTIVE_TIME</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a262224b76c4dcf3cea82ee9465943bda</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_SPEAKER_TONE_BEEP</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a265f834c4306024944c8ddddf02a3d0a</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_SPEAKER_TONE_MELODY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a3d4ccd45e6f44e668908c27f589b0fe2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_MOTOR_0_PERMANENT_VELOCITY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a5f40149c92d36bd636720b8355e53069</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_MOTOR_1_PERMANENT_VELOCITY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04abed04f8b344b7771c7816f73ad8cf132</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_MOTOR_0_LEAKY_VELOCITY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a4a98ec1f861bba08fda64de0b1f30a92</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PUSH_BOT_MOTOR_1_LEAKY_VELOCITY</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>abc6126af1d45847bc59afa0aa3216b04a1e4f6b8885576368c774183501ae3a6d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_NO_TIMESTAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adc29c2ff13d900c2f185ee95427fb06ca35c35a3d19b4e8bbea2e9c2a345d0cf7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_DELTA_TIMESTAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adc29c2ff13d900c2f185ee95427fb06ca7e7a925c702fda8735064bd0c71b5de4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_TWO_BYTE_TIME_STAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adc29c2ff13d900c2f185ee95427fb06ca3a5dbca82d4fd637a9b24f952c0a3b1d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_THREE_BYTE_TIME_STAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adc29c2ff13d900c2f185ee95427fb06ca5dbc455edb7e576b4b10207499df32d4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_FOUR_BYTE_TIME_STAMPS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adc29c2ff13d900c2f185ee95427fb06cafcbea561be57d033de0ec3777485e92e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_RETINA_NO_DOWN_SAMPLING</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a61dadd085c1777f559549e05962b2c9ea8de5b4140e590b1afd4610167028e60f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_RETINA_64_DOWN_SAMPLING</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a61dadd085c1777f559549e05962b2c9eafc3113b6039407f4ba93ccfede07921b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_RETINA_32_DOWN_SAMPLING</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a61dadd085c1777f559549e05962b2c9ea69237ae9abec2c9a96870f267d951fc1</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PAYLOAD_RETINA_16_DOWN_SAMPLING</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a61dadd085c1777f559549e05962b2c9eaff0513e0ecc8dfe19b9c70d891b09534</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>munich_protocol_modes_e</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2ef</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_RESET_TO_DEFAULT</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efa8a71e56e25b553379ea228b4a1ded8ba</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_PUSH_BOT</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efa168d928b4999466fb0ee4afe6c0ebf17</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_SPOMNIBOT</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efab59da94c5640da6e33ea55115432aac2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_BALL_BALANCER</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efa24993add8c6fbf8110e30b2bec6b5cde</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_MY_ORO_BOTICS</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efaac09deb99dbfa656e3055544b6b1a9cc</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MUNICH_PROTOCOL_FREE</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a276ea595faa60fd27301105f3613b2efa591c8c75a63ce2f61e0a20f9ff12da89</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>set_protocol_mode</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a63f78c33f4497c8732b5532c3985e627</anchor>
      <arglist>(munich_protocol_modes_e new_mode, uint32_t new_instance_key)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_get_configure_master_key_command</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a8da65ae6eef8fa3846d3194eefdf4b57</anchor>
      <arglist>(uint32_t new_key)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_get_set_mode_command</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a627df4739d78e9e5593f889923a6e1d8</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_set_retina_transmission_key</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a343febb69fae0be23a0dae956bc0fa25</anchor>
      <arglist>(uint32_t new_key, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_disable_retina_event_streaming</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aeae2e5559f9d20e1cad45654b2f0a73d</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_reset_retina</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a301f3f025960b140d2c5f00273e90c66</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_master_slave_use_internal_counter</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a1d3eb329056e2e12f19d01aed8a9633b</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_master_slave_set_slave</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ab9c08589df340e59104530a6f23bf630</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_master_slave_set_master_clock_not_started</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a9210c92998123f071fce28a5f4a92fc2</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_master_slave_set_master_clock_active</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a7dd1390f27ac38f727d1e3e11d3882f7</anchor>
      <arglist>(uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_bias_values</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a9f36c965f338b9ffee8bd0739edd9309</anchor>
      <arglist>(uint32_t bias_id, uint32_t bias_value, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_turn_off_sensor_reporting</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a0431318d389c280a5085ae00842a85f5</anchor>
      <arglist>(uint32_t sensor_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_poll_sensors_once</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aebf57d61e786656b0062073c0a5789ab</anchor>
      <arglist>(uint32_t sensor_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_poll_individual_sensor_continuously</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a323f23ea8f3b20cc806f0dcf982718cc</anchor>
      <arglist>(uint32_t sensor_id, uint32_t time_in_ms)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor_enable_disable</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a963f374194d909f3694963cfc9c4e965</anchor>
      <arglist>(uint32_t enable_disable, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor_total_period_duration</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a4fb2104095f3975a76477e08124028ef</anchor>
      <arglist>(uint32_t time_in_ms, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor0_raw_output_permanent</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a7890f33cda380a0e8fb5c30a94e3ddb4</anchor>
      <arglist>(uint32_t pwm_signal, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor1_raw_output_permanent</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aba8a19ca1a35ce982dd58ab086c60ef4</anchor>
      <arglist>(uint32_t pwm_signal, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor0_raw_output_leak_to_0</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a5c33f32e6993d15042238058920ffd53</anchor>
      <arglist>(uint32_t pwm_signal, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_generic_motor1_raw_output_leak_to_0</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a837fc869cf029d2a88d09f03674eb316</anchor>
      <arglist>(uint32_t pwm_signal, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_a_duration</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a8043794711243ccbee4ec95026ca23ae</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_b_duration</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a1c42d8d1d730d34c59621bdcd2ac019a</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_c_duration</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a5f7d1a3fd79abeb1256bbe7be8dc657c</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_a_channel_0_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a97f6780c64638e455c245e6bf8abe673</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_a_channel_1_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a67c9432aa82f7bee54c2a8ccbafc4eeb</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_b_channel_0_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ab47f25902bc7387b2d4e69423b00e7c1</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_b_channel_1_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a4e079b283a1f225af49d2f551f2e4067</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_c_channel_0_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ac4d568446b50147c2977f1253669790a</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_pwm_pin_output_timer_c_channel_1_ratio</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a4c85214107445053137ea974236543e3</anchor>
      <arglist>(uint32_t timer_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_query_state_of_io_lines</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a6b528197cc61a44e96c36df0a78232e3</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_set_output_pattern_for_payload</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a40d59634d577ce03a3e63d0ef6c15709</anchor>
      <arglist>(uint32_t payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_add_payload_logic_to_current_output</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a401923b4aebaf0d3bd0544f2595f6af7</anchor>
      <arglist>(uint32_t payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_remove_payload_logic_to_current_output</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ad0f680213cdf6483d3a9ce6c107df75f</anchor>
      <arglist>(uint32_t payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_set_payload_pins_to_high_impedance</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a82cab0e2116f047ce871b85ad449492b</anchor>
      <arglist>(uint32_t payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_laser_config_total_period</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a34e031fa12d0c4a94221a368d31666ba</anchor>
      <arglist>(uint32_t total_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_laser_config_active_time</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a2aa806d7f6722fdf3f5b58226fee85e8</anchor>
      <arglist>(uint32_t active_time, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_laser_set_frequency</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a712450f86219392e5e07f97502962be6</anchor>
      <arglist>(uint32_t frequency, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_speaker_config_total_period</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ad76c83120ef750a56cb808610c5c9dea</anchor>
      <arglist>(uint32_t total_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_speaker_config_active_time</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a65c33170f492a1ccacbd7a6dba2ccddb</anchor>
      <arglist>(uint32_t active_time, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_speaker_set_tone</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a71aa2936830339beb4fd2b07eb8cc923</anchor>
      <arglist>(uint32_t frequency, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_speaker_set_melody</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a16c2d7aeb44a9c9a40c358bc95241b20</anchor>
      <arglist>(uint32_t melody, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_led_total_period</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a9e271be0ca62415cd7218f1059d9f71d</anchor>
      <arglist>(uint32_t total_period, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_led_back_active_time</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a0b99264f73273a25f9465894c0b7d136</anchor>
      <arglist>(uint32_t active_time, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_led_front_active_time</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a20b8821bbfce788b040b7d4fc7fe619d</anchor>
      <arglist>(uint32_t active_time, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_led_set_frequency</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a9a1ea485a42a7f01ea15cddaf211bd5e</anchor>
      <arglist>(uint32_t frequency, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_motor_0_permanent</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aed3bf940b69de066fc80219222b13b2d</anchor>
      <arglist>(state_t velocity, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_motor_1_permanent</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>af7df99ccd07829378705355efe88f87d</anchor>
      <arglist>(uint32_t velocity, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_motor_0_leaking_towards_zero</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aa3ed949b22452b85a9414826b28fb9ee</anchor>
      <arglist>(uint32_t velocity, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_push_bot_motor_1_leaking_towards_zero</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>aaa130269a76adc15a1c7372c51ac5278</anchor>
      <arglist>(uint32_t velocity, uint32_t uart_id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static multicast_packet</type>
      <name>munich_protocol_set_retina_transmission</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a6002f9eecf40f8f0ed68353849500720</anchor>
      <arglist>(bool events_in_key, uint32_t retina_pixels, bool payload_holds_time_stamps, uint32_t size_of_time_stamp_in_bytes, uint32_t uart_id)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static munich_protocol_modes_e</type>
      <name>mode</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a4d725b62e5fd2919183e67af7bdad319</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>instance_key</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a21aacafb9f4a3adc7afc7b0e4681e0bc</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron-typedefs.h</name>
    <path>/github/workspace/neural_modelling/src/common/</path>
    <filename>neuron-typedefs_8h.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="yes" imported="no">maths-util.h</includes>
    <member kind="typedef">
      <type>uint32_t</type>
      <name>key_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>a07a71b4e2eedce7fe0dcc3077107f7ac</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>uint32_t</type>
      <name>payload_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>a445182712b36c41ebb26ca639423c0cc</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>uint32_t</type>
      <name>spike_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>a6f8f96f76107734fe756b67227742b32</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>struct synaptic_row *</type>
      <name>synaptic_row_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>a15c5afaa95cf67525970ec7c98d4a859</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>REAL</type>
      <name>input_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>ac412098e688b864e8f4e2f3c0ed86591</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>REAL</type>
      <name>state_t</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>ab5816efea940631eca6d71dd4ca99c17</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static key_t</type>
      <name>spike_key</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>adca4ceace8e60559a8953bc89a616d70</anchor>
      <arglist>(spike_t s)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static payload_t</type>
      <name>spike_payload</name>
      <anchorfile>neuron-typedefs_8h.html</anchorfile>
      <anchor>a93bb0a3a77ac4ffa532b175508f0b6d0</anchor>
      <arglist>(spike_t s)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>delay_extension.c</name>
    <path>/github/workspace/neural_modelling/src/delay_extension/</path>
    <filename>delay__extension_8c.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="yes" imported="no">delay_extension.h</includes>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" imported="no">common/in_spikes.h</includes>
    <class kind="struct">delay_extension_provenance</class>
    <member kind="define">
      <type>#define</type>
      <name>IN_BUFFER_SIZE</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aa8a96f886dfb6ce7692f035fe49597c2</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>COUNTER_SATURATION_VALUE</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a7857bce08704e7040406ce50c0fd52b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>delay_extension_callback_priorities</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MC_PACKET</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6ad73783ea228c0f1164d4ed5274bc2fc4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TIMER</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6a17ba9bae1b8d7e8d6c12d46ec58e0769</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>USER</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6ae2d30a195cee6b2961cc2c23ea4b520b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SDP</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6ad645defae8408de2415f3dc417f69773</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BACKGROUND</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6aa44b734476c2f3d073ee7aca08660a0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9754029f237bd209c67ffa701d8250c6a6537a62f6f155792bb9a320ee2ec4d68</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>zero_spike_counters</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a5cc35d1e25ce49ad5799713dabd2abb9</anchor>
      <arglist>(uint8_t *counters, uint32_t num_items)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>round_to_next_pot</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ac5c8b24e3b6d606c321ce3cd22ebe8a0</anchor>
      <arglist>(uint32_t v)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_parameters</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>afeb21131569d4edffb884f6564de89dd</anchor>
      <arglist>(struct delay_parameters *params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>store_provenance_data</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a6a6f18428eca2d03be2d82834e642876</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialize</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a03a8e4045b51680cc94b4359837fa796</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>incoming_spike_callback</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a95885055138e174e0b8e70fcafa07388</anchor>
      <arglist>(uint key, uint payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>key_n</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>af9250c2936d38c801dba8546e83cdcc0</anchor>
      <arglist>(key_t k)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>spike_process</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a35a7cd4c965a1200ebefc398d69554f2</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>timer_callback</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ac4eddb02ed618a1e59aef495625555f4</anchor>
      <arglist>(uint timer_count, uint unused1)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>has_key</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aaa69ed97fd7f2c36209c6774a12ff447</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>key</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a6d4ec8e4f3148d51041635da9986c3fa</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>incoming_key</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a4488aeac882fcf58d797dceb0278d7af</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>incoming_mask</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a108857a21fa14892f4c1de1427faef58</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>incoming_neuron_mask</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a13afd57fbc79bb49bb800adaa4c0b9c6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_neurons</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a140387de8120673d899f4693ab97ae54</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>max_keys</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a897b38a9bdd468c0017438c272905663</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>clear_input_buffers_of_late_packets</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a6553b0c9813c830009e32639e34855a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>time</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint8_t **</type>
      <name>spike_counters</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a054f3ef43206b776850559a847dc8276</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bit_field_t *</type>
      <name>neuron_delay_stage_config</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ab7cc70efc4d7a8de402bb8c1d180abce</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_delay_stages</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ac9e975dfdcc2204fa4b4366446786a6c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_delay_in_a_stage</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aeb4240f3e630b0b67c607c606562b3d1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_delay_slots</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a69be46ad5911bdfcdb97bc33d2cbfc63</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_delay_slots_mask</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a72085e13d5dfdbd948a0773dd1e13096</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>neuron_bit_field_words</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>afa9a8a4f3032a26fe66584aab4a7d201</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_in_spikes</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a587eec262ef2a410251b4b507b6da974</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_processed_spikes</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a6493419a971eb32c75d2295ebc0fa4ed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spikes_sent</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a3234bc766f5cbe802ac49b206bf95f45</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spikes_added</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aad9874f1f923ca947460f8f82fddcb2f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_delays</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a5afaacadf2ba06d040be6c3c3b173feb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>saturation_count</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>af98038a462abb37d565a0f4e6fbc2b2a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_packets_dropped_due_to_invalid_neuron_value</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a34eb84f659416414ae2ab50093e1f6aa</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_packets_dropped_due_to_invalid_key</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ae8c134de34cba293cb75cb5b5dc24e21</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>count_input_buffer_packets_late</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aec7439b9895311b77cf2ee71500b4206</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_period</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ac0c27301e134af3ce80814a553601074</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>spike_processing</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ab1e120fbfb78e0e1e63b3ce5f050d825</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_backgrounds_queued</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aaa9d9edd5bdfe2c8fedec47a25acfee8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_background_overloads</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>afcea30e1e9196cb82aafc8502bda0a3b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>max_backgrounds_queued</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ac8502bcf887a00b1f6f9193d43365488</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>delay_extension.h</name>
    <path>/github/workspace/neural_modelling/src/delay_extension/</path>
    <filename>delay__extension_8h.html</filename>
    <class kind="struct">delay_parameters</class>
    <member kind="define">
      <type>#define</type>
      <name>pack_delay_index_stage</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a62c01d7388112097a930509cf05f6168</anchor>
      <arglist>(index, stage)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>unpack_delay_index</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a64494ca55a7d8abb2d9c45c1928da31d</anchor>
      <arglist>(packed)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>unpack_delay_stage</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a4f6b0f0080036b3baadaebe99a5c4b95</anchor>
      <arglist>(packed)</arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>region_identifiers</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYSTEM</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32a57cc238145ec1361c72c327674c0d754</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DELAY_PARAMS</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32ad8afa7b77b25e7899aded1cb7a4f0e66</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROVENANCE_REGION</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32a43f0d58cfc0317ea06139b20c9242d1e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXPANDER_REGION</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32a719368d00e2ee9a5b0e27a360ea05be4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TDMA_REGION</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32a3ec559988321d901a9631875c4782ba6</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>additional_input.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/additional_inputs/</path>
    <filename>additional__input_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="typedef">
      <type>additional_input_t *</type>
      <name>additional_input_pointer_t</name>
      <anchorfile>additional__input_8h.html</anchorfile>
      <anchor>a2c12126afb370d66fb361daac93067cb</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>additional_input_get_input_value_as_current</name>
      <anchorfile>additional__input_8h.html</anchorfile>
      <anchor>a136eddebea2acf483d5e28be84070452</anchor>
      <arglist>(struct additional_input_t *additional_input, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_has_spiked</name>
      <anchorfile>additional__input_8h.html</anchorfile>
      <anchor>ac6a9ad3289ee8e787955dfbd7b2a726d</anchor>
      <arglist>(struct additional_input_t *additional_input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>additional_input_ca2_adaptive_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/additional_inputs/</path>
    <filename>additional__input__ca2__adaptive__impl_8h.html</filename>
    <includes id="additional__input_8h" name="additional_input.h" local="yes" imported="no">additional_input.h</includes>
    <class kind="struct">additional_input_t</class>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>additional_input_get_input_value_as_current</name>
      <anchorfile>additional__input__ca2__adaptive__impl_8h.html</anchorfile>
      <anchor>a136eddebea2acf483d5e28be84070452</anchor>
      <arglist>(struct additional_input_t *additional_input, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_has_spiked</name>
      <anchorfile>additional__input__ca2__adaptive__impl_8h.html</anchorfile>
      <anchor>ac6a9ad3289ee8e787955dfbd7b2a726d</anchor>
      <arglist>(struct additional_input_t *additional_input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>additional_input_none_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/additional_inputs/</path>
    <filename>additional__input__none__impl_8h.html</filename>
    <includes id="additional__input_8h" name="additional_input.h" local="yes" imported="no">additional_input.h</includes>
    <class kind="struct">additional_input_t</class>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>additional_input_get_input_value_as_current</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a136eddebea2acf483d5e28be84070452</anchor>
      <arglist>(struct additional_input_t *additional_input, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_has_spiked</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>ac6a9ad3289ee8e787955dfbd7b2a726d</anchor>
      <arglist>(struct additional_input_t *additional_input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>c_main.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>c__main_8c.html</filename>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" imported="no">common/in_spikes.h</includes>
    <includes id="regions_8h" name="regions.h" local="yes" imported="no">regions.h</includes>
    <includes id="neuron_8h" name="neuron.h" local="yes" imported="no">neuron.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="yes" imported="no">synapses.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" imported="no">spike_processing.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="yes" imported="no">population_table/population_table.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" imported="no">plasticity/synapse_dynamics.h</includes>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" imported="no">structural_plasticity/synaptogenesis_dynamics.h</includes>
    <includes id="neuron_2profile__tags_8h" name="profile_tags.h" local="yes" imported="no">profile_tags.h</includes>
    <includes id="direct__synapses_8h" name="direct_synapses.h" local="yes" imported="no">direct_synapses.h</includes>
    <class kind="struct">neuron_provenance</class>
    <member kind="define">
      <type>#define</type>
      <name>NUMBER_OF_REGIONS_TO_RECORD</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a9460522d5774f317649cd352ea6112b0</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>callback_priorities</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MULTICAST</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a607d700b2c0a01c54bdadde074a7cb12</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SDP</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964ad645defae8408de2415f3dc417f69773</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a6537a62f6f155792bb9a320ee2ec4d68</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TIMER</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a17ba9bae1b8d7e8d6c12d46ec58e0769</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>c_main_store_provenance_data</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a1dc4d17392d4c0a6dac7ab12267da487</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>abc8ec4992e18193766cc267a4968f1d7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>resume_callback</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a8967e8eb09363007076f840186a20995</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>background_callback</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aa6bf2a62e10a1dd22d4ec7fb3716cab9</anchor>
      <arglist>(uint timer_count, uint local_time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>timer_callback</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a217aea663c8dd444052831cbde49bd62</anchor>
      <arglist>(uint timer_count, uint unused)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_period</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ac0c27301e134af3ce80814a553601074</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int32_t</type>
      <name>last_rewiring_time</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a1cb8b41466def0e135ca00facead99b8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int32_t</type>
      <name>rewiring_period</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aa08e7ff835bc68c5a91214035f412894</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>rewiring</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a1c0ebb4e72cbc1b6f3da884524a78078</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>count_rewire_attempts</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a113643d98988bc0d1706e0b21d7b4a4e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_neurons</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a7368643a28282d8b3429f0fb145aa5db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_backgrounds_queued</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aaa9d9edd5bdfe2c8fedec47a25acfee8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_background_overloads</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>afcea30e1e9196cb82aafc8502bda0a3b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>max_backgrounds_queued</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ac8502bcf887a00b1f6f9193d43365488</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint</type>
      <name>global_timer_count</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a5d218df3d38c1fe5b37eb202ddd28700</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>decay.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>decay_8h.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="no" imported="no">common/maths-util.h</includes>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="define">
      <type>#define</type>
      <name>decay</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>a251df1ff8ee78f551bedbd55c451a859</anchor>
      <arglist>(x, d)</arglist>
    </member>
    <member kind="typedef">
      <type>UFRACT</type>
      <name>decay_t</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>a2d8155d52b7e3ac155ddc14cbe1efb25</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static s1615</type>
      <name>decay_s1615</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>a6f0906eff09adaaf873d19d20f2a120f</anchor>
      <arglist>(s1615 x, decay_t decay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static u1616</type>
      <name>decay_u1616</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>a4ea143b76b7a8ab080171ac1c099db1c</anchor>
      <arglist>(u1616 x, decay_t decay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static s015</type>
      <name>decay_s015</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>aa227505964f87337ca85b3c20da50c19</anchor>
      <arglist>(s015 x, decay_t decay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static u016</type>
      <name>decay_u016</name>
      <anchorfile>decay_8h.html</anchorfile>
      <anchor>a9ff362327565c924c464ad439daab18e</anchor>
      <arglist>(u016 x, decay_t decay)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>direct_synapses.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>direct__synapses_8c.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <class kind="struct">single_synaptic_row_t</class>
    <class kind="struct">direct_matrix_data_t</class>
    <member kind="function">
      <type>bool</type>
      <name>direct_synapses_initialise</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a4f96698f7745cad8c8009298fb03da9b</anchor>
      <arglist>(void *direct_matrix_address, address_t *direct_synapses_address)</arglist>
    </member>
    <member kind="function">
      <type>synaptic_row_t</type>
      <name>direct_synapses_get_direct_synapse</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a4e044c9a28f8428d353c90dbc0249482</anchor>
      <arglist>(void *row_address)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static single_synaptic_row_t</type>
      <name>single_fixed_synapse</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a5dd766c9e442321941ea5ccef7d32710</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>direct_synapses.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>direct__synapses_8h.html</filename>
    <member kind="function">
      <type>bool</type>
      <name>direct_synapses_initialise</name>
      <anchorfile>direct__synapses_8h.html</anchorfile>
      <anchor>a4f96698f7745cad8c8009298fb03da9b</anchor>
      <arglist>(void *direct_matrix_address, address_t *direct_synapses_address)</arglist>
    </member>
    <member kind="function">
      <type>synaptic_row_t</type>
      <name>direct_synapses_get_direct_synapse</name>
      <anchorfile>direct__synapses_8h.html</anchorfile>
      <anchor>a4e044c9a28f8428d353c90dbc0249482</anchor>
      <arglist>(void *row_address)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/implementations/</path>
    <filename>neuron__impl_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_initialise</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>aab6d669689876332dfb4aa6b21990d77</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_add_inputs</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a7d0403fedf08df2d791534cfe72f4fa2</anchor>
      <arglist>(index_t synapse_type_index, index_t neuron_index, input_t weights_this_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_load_neuron_parameters</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a72b0028625c6e3cad1e4176bdba1b44e</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a21f9a596a5048838a60fee323e466314</anchor>
      <arglist>(index_t neuron_index, input_t external_bias)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_store_neuron_parameters</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>af2c8c3ce110bf3e9b4d0dc27f22b4860</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_inputs</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>aa1d6d1186174dd22b3d152b919a4ca0f</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_synapse_parameters</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a29ad1f4cd958c5acde321fe2f2d41abe</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>const char *</type>
      <name>neuron_impl_get_synapse_type_char</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>ab28525e166d16dfb00284093d84c6661</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_external_devices.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/implementations/</path>
    <filename>neuron__impl__external__devices_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" imported="no">neuron_impl.h</includes>
    <includes id="neuron__model__lif__impl_8h" name="neuron_model_lif_impl.h" local="no" imported="no">neuron/models/neuron_model_lif_impl.h</includes>
    <includes id="additional__input_8h" name="additional_input.h" local="no" imported="no">neuron/additional_inputs/additional_input.h</includes>
    <includes id="synapse__types__exponential__impl_8h" name="synapse_types_exponential_impl.h" local="no" imported="no">neuron/synapse_types/synapse_types_exponential_impl.h</includes>
    <includes id="input__type__current_8h" name="input_type_current.h" local="no" imported="no">neuron/input_types/input_type_current.h</includes>
    <includes id="additional__input__none__impl_8h" name="additional_input_none_impl.h" local="no" imported="no">neuron/additional_inputs/additional_input_none_impl.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" imported="no">neuron/neuron_recording.h</includes>
    <class kind="struct">packet_firing_data_t</class>
    <member kind="enumeration">
      <type></type>
      <name>send_type</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_INT</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9ea3dd35dd465fc1317eaa70269b6e6dcfe</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_UINT</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9ea9f0c39dd1fcf4de8859fe4563ee3ad55</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_ACCUM</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9ea020920e4dc6523fa9322a718de973b59</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_UACCUM</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9ea7890c390703766bca2b113710272ed13</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_FRACT</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9eab4b21fb2f7c58f05dee2ce53c31a1675</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SEND_TYPE_UFRACT</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a73f8837bd24ba4a9abf204756c0b9b9ea27e9dfe79f29abb0c5c87831e261c176</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>word_recording_indices</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>V_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03ab3af76b3ea8cdd3c68aaa7432e4acf96</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_EXC_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a1f4a97c6e4523af2fea20d3ca50dbd0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_INH_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a0e4025cde485021d43ae9284bee78c6e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_RECORDED_VARS</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a868c932bcf4cab46d2b226b04bc2438f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>V_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03ab3af76b3ea8cdd3c68aaa7432e4acf96</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_EXC_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a1f4a97c6e4523af2fea20d3ca50dbd0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_INH_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a0e4025cde485021d43ae9284bee78c6e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_RECORDED_VARS</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a868c932bcf4cab46d2b226b04bc2438f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>bitfield_recording_indices</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PACKET_RECORDING_BITFIELD</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3a122d35b1c72444010af712fe58cd21be</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_BITFIELD_VARS</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3aa2d088b9c45269b7bf9461907960c21c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SPIKE_RECORDING_BITFIELD</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3a12b36ddd66438ef711657d3a5ff70ebb</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_BITFIELD_VARS</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3aa2d088b9c45269b7bf9461907960c21c</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_initialise</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>aab6d669689876332dfb4aa6b21990d77</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_add_inputs</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a7d0403fedf08df2d791534cfe72f4fa2</anchor>
      <arglist>(index_t synapse_type_index, index_t neuron_index, input_t weights_this_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>n_words_needed</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a712ac031031f4c6e8e7979936f32a783</anchor>
      <arglist>(size_t size)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_load_neuron_parameters</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a72b0028625c6e3cad1e4176bdba1b44e</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a21f9a596a5048838a60fee323e466314</anchor>
      <arglist>(index_t neuron_index, input_t external_bias)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_store_neuron_parameters</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>af2c8c3ce110bf3e9b4d0dc27f22b4860</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_inputs</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>aa1d6d1186174dd22b3d152b919a4ca0f</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_synapse_parameters</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a29ad1f4cd958c5acde321fe2f2d41abe</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>const char *</type>
      <name>neuron_impl_get_synapse_type_char</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>ab28525e166d16dfb00284093d84c6661</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static neuron_t *</type>
      <name>neuron_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a2a28d6bb285e12f4b75b1fc4a77c0314</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static input_type_t *</type>
      <name>input_type_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a31058212f43265088fe71863d4ea0907</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static additional_input_t *</type>
      <name>additional_input_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a9a9983ef2e0e8377f0fc818e32eec11d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static packet_firing_data_t *</type>
      <name>packet_firing_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a8870077736fbcaca0d2aba2bb33f1040</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static global_neuron_params_t *</type>
      <name>global_parameters</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a3080a592212f89a8d8dde67f13a58949</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static synapse_param_t *</type>
      <name>neuron_synapse_shaping_params</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>ae0383b1a8ff4169668ce6e5130cfbeaf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint</type>
      <name>n_steps_per_timestep</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>adc2145aaa2f8435401d2c077d42c7b91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint</type>
      <name>global_timer_count</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a5d218df3d38c1fe5b37eb202ddd28700</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_standard.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/implementations/</path>
    <filename>neuron__impl__standard_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" imported="no">neuron_impl.h</includes>
    <includes id="neuron__model_8h" name="neuron_model.h" local="no" imported="no">neuron/models/neuron_model.h</includes>
    <includes id="input__type_8h" name="input_type.h" local="no" imported="no">neuron/input_types/input_type.h</includes>
    <includes id="additional__input_8h" name="additional_input.h" local="no" imported="no">neuron/additional_inputs/additional_input.h</includes>
    <includes id="threshold__type_8h" name="threshold_type.h" local="no" imported="no">neuron/threshold_types/threshold_type.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="no" imported="no">neuron/synapse_types/synapse_types.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" imported="no">neuron/neuron_recording.h</includes>
    <member kind="enumeration">
      <type></type>
      <name>word_recording_indices</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>V_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03ab3af76b3ea8cdd3c68aaa7432e4acf96</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_EXC_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a1f4a97c6e4523af2fea20d3ca50dbd0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_INH_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a0e4025cde485021d43ae9284bee78c6e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_RECORDED_VARS</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a868c932bcf4cab46d2b226b04bc2438f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>V_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03ab3af76b3ea8cdd3c68aaa7432e4acf96</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_EXC_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a1f4a97c6e4523af2fea20d3ca50dbd0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>GSYN_INH_RECORDING_INDEX</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a0e4025cde485021d43ae9284bee78c6e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_RECORDED_VARS</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03a868c932bcf4cab46d2b226b04bc2438f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>bitfield_recording_indices</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PACKET_RECORDING_BITFIELD</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3a122d35b1c72444010af712fe58cd21be</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_BITFIELD_VARS</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3aa2d088b9c45269b7bf9461907960c21c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SPIKE_RECORDING_BITFIELD</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3a12b36ddd66438ef711657d3a5ff70ebb</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_BITFIELD_VARS</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a1a1145a27f2273fe3bf900dc1602b4e3aa2d088b9c45269b7bf9461907960c21c</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_initialise</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>aab6d669689876332dfb4aa6b21990d77</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_add_inputs</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a7d0403fedf08df2d791534cfe72f4fa2</anchor>
      <arglist>(index_t synapse_type_index, index_t neuron_index, input_t weights_this_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>n_words_needed</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a712ac031031f4c6e8e7979936f32a783</anchor>
      <arglist>(size_t size)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_load_neuron_parameters</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a72b0028625c6e3cad1e4176bdba1b44e</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a21f9a596a5048838a60fee323e466314</anchor>
      <arglist>(index_t neuron_index, input_t external_bias)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_store_neuron_parameters</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>af2c8c3ce110bf3e9b4d0dc27f22b4860</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_inputs</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>aa1d6d1186174dd22b3d152b919a4ca0f</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_impl_print_synapse_parameters</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a29ad1f4cd958c5acde321fe2f2d41abe</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>const char *</type>
      <name>neuron_impl_get_synapse_type_char</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>ab28525e166d16dfb00284093d84c6661</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static neuron_t *</type>
      <name>neuron_array</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a2a28d6bb285e12f4b75b1fc4a77c0314</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static input_type_t *</type>
      <name>input_type_array</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a31058212f43265088fe71863d4ea0907</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static additional_input_t *</type>
      <name>additional_input_array</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a9a9983ef2e0e8377f0fc818e32eec11d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static threshold_type_t *</type>
      <name>threshold_type_array</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a4f5c3aa587fdd4e5a65e6dd1ec4443db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static global_neuron_params_t *</type>
      <name>global_parameters</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a3080a592212f89a8d8dde67f13a58949</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static synapse_param_t *</type>
      <name>neuron_synapse_shaping_params</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>ae0383b1a8ff4169668ce6e5130cfbeaf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint</type>
      <name>n_steps_per_timestep</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>adc2145aaa2f8435401d2c077d42c7b91</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/input_types/</path>
    <filename>input__type_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>input_type_t *</type>
      <name>input_type_pointer_t</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>af2eac2241adec660b95b59ab8cc519ff</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>a81523b64ae8f05a21338702d0551e9e6</anchor>
      <arglist>(input_t *restrict value, input_type_t *input_type, uint16_t num_receptors)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_excitatory_input_to_current</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>af4e297fdfe7c9c7c2a9dcdca4d7e6c56</anchor>
      <arglist>(input_t *restrict exc_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_inhibitory_input_to_current</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>a07605d2b04f6d102c116229dd0ccc91c</anchor>
      <arglist>(input_t *restrict inh_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type_conductance.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/input_types/</path>
    <filename>input__type__conductance_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" imported="no">input_type.h</includes>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__conductance_8h.html</anchorfile>
      <anchor>a81523b64ae8f05a21338702d0551e9e6</anchor>
      <arglist>(input_t *restrict value, input_type_t *input_type, uint16_t num_receptors)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_excitatory_input_to_current</name>
      <anchorfile>input__type__conductance_8h.html</anchorfile>
      <anchor>af4e297fdfe7c9c7c2a9dcdca4d7e6c56</anchor>
      <arglist>(input_t *restrict exc_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_inhibitory_input_to_current</name>
      <anchorfile>input__type__conductance_8h.html</anchorfile>
      <anchor>a07605d2b04f6d102c116229dd0ccc91c</anchor>
      <arglist>(input_t *restrict inh_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type_current.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/input_types/</path>
    <filename>input__type__current_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" imported="no">input_type.h</includes>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__current_8h.html</anchorfile>
      <anchor>a81523b64ae8f05a21338702d0551e9e6</anchor>
      <arglist>(input_t *restrict value, input_type_t *input_type, uint16_t num_receptors)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_excitatory_input_to_current</name>
      <anchorfile>input__type__current_8h.html</anchorfile>
      <anchor>af4e297fdfe7c9c7c2a9dcdca4d7e6c56</anchor>
      <arglist>(input_t *restrict exc_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_inhibitory_input_to_current</name>
      <anchorfile>input__type__current_8h.html</anchorfile>
      <anchor>a07605d2b04f6d102c116229dd0ccc91c</anchor>
      <arglist>(input_t *restrict inh_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>INPUT_SCALE_FACTOR</name>
      <anchorfile>input__type__current_8h.html</anchorfile>
      <anchor>a80a0eacdb1171eb336d3ff00ee1fa50a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type_delta.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/input_types/</path>
    <filename>input__type__delta_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" imported="no">input_type.h</includes>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__delta_8h.html</anchorfile>
      <anchor>a81523b64ae8f05a21338702d0551e9e6</anchor>
      <arglist>(input_t *restrict value, input_type_t *input_type, uint16_t num_receptors)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_excitatory_input_to_current</name>
      <anchorfile>input__type__delta_8h.html</anchorfile>
      <anchor>af4e297fdfe7c9c7c2a9dcdca4d7e6c56</anchor>
      <arglist>(input_t *restrict exc_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_inhibitory_input_to_current</name>
      <anchorfile>input__type__delta_8h.html</anchorfile>
      <anchor>a07605d2b04f6d102c116229dd0ccc91c</anchor>
      <arglist>(input_t *restrict inh_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>INPUT_SCALE_FACTOR</name>
      <anchorfile>input__type__delta_8h.html</anchorfile>
      <anchor>a80a0eacdb1171eb336d3ff00ee1fa50a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type_none.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/input_types/</path>
    <filename>input__type__none_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" imported="no">input_type.h</includes>
    <class kind="struct">input_type_t</class>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>a81523b64ae8f05a21338702d0551e9e6</anchor>
      <arglist>(input_t *restrict value, input_type_t *input_type, uint16_t num_receptors)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_excitatory_input_to_current</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>af4e297fdfe7c9c7c2a9dcdca4d7e6c56</anchor>
      <arglist>(input_t *restrict exc_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_convert_inhibitory_input_to_current</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>a07605d2b04f6d102c116229dd0ccc91c</anchor>
      <arglist>(input_t *restrict inh_input, const input_type_t *input_type, state_t membrane_voltage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/models/</path>
    <filename>neuron__model_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="typedef">
      <type>global_neuron_params_t *</type>
      <name>global_neuron_params_pointer_t</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>af6a73a4c591000fae3ac1f7e879b9a36</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_set_global_neuron_params</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a2c709e18b3833cf07131b394b0a9b929</anchor>
      <arglist>(const global_neuron_params_t *params)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a452331c36f58a564227b5d2a3a20bd3f</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a49c629814dc187dc38a4b8f0dbebd111</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a91774a9b87c1875fcb7659fe0f096857</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_state_variables</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a039b8ee28cccb786e7c67c985e88e3d6</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_parameters</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a645937167c46b7556757b05250f9864d</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_izh_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/models/</path>
    <filename>neuron__model__izh__impl_8c.html</filename>
    <includes id="neuron__model__izh__impl_8h" name="neuron_model_izh_impl.h" local="yes" imported="no">neuron_model_izh_impl.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>rk2_kernel_midpoint</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>ae9b257f5e4059af3a5fa30730512f2b6</anchor>
      <arglist>(REAL h, neuron_t *neuron, REAL input_this_timestep)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_set_global_neuron_params</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a2c709e18b3833cf07131b394b0a9b929</anchor>
      <arglist>(const global_neuron_params_t *params)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a452331c36f58a564227b5d2a3a20bd3f</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a49c629814dc187dc38a4b8f0dbebd111</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a91774a9b87c1875fcb7659fe0f096857</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_state_variables</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a039b8ee28cccb786e7c67c985e88e3d6</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_parameters</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a645937167c46b7556757b05250f9864d</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const global_neuron_params_t *</type>
      <name>global_params</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a60d02bd3fd0eb5694bf3d08679d4565d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>SIMPLE_TQ_OFFSET</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>a2a9449a2c1269d81389014e6c2df9573</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>MAGIC_MULTIPLIER</name>
      <anchorfile>neuron__model__izh__impl_8c.html</anchorfile>
      <anchor>adf9a0e8d9c7ec24f407eee48d6064666</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_izh_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/models/</path>
    <filename>neuron__model__izh__impl_8h.html</filename>
    <includes id="neuron__model_8h" name="neuron_model.h" local="yes" imported="no">neuron_model.h</includes>
    <class kind="struct">neuron_t</class>
    <class kind="struct">global_neuron_params_t</class>
  </compound>
  <compound kind="file">
    <name>neuron_model_lif_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/models/</path>
    <filename>neuron__model__lif__impl_8c.html</filename>
    <includes id="neuron__model__lif__impl_8h" name="neuron_model_lif_impl.h" local="yes" imported="no">neuron_model_lif_impl.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>lif_neuron_closed_form</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>acdc543d115e02324c243ebbfdd303214</anchor>
      <arglist>(neuron_t *neuron, REAL V_prev, input_t input_this_timestep)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_set_global_neuron_params</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a2c709e18b3833cf07131b394b0a9b929</anchor>
      <arglist>(const global_neuron_params_t *params)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a452331c36f58a564227b5d2a3a20bd3f</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a49c629814dc187dc38a4b8f0dbebd111</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function">
      <type>state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a91774a9b87c1875fcb7659fe0f096857</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_state_variables</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a039b8ee28cccb786e7c67c985e88e3d6</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_model_print_parameters</name>
      <anchorfile>neuron__model__lif__impl_8c.html</anchorfile>
      <anchor>a645937167c46b7556757b05250f9864d</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_lif_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/models/</path>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <includes id="neuron__model_8h" name="neuron_model.h" local="yes" imported="no">neuron_model.h</includes>
    <class kind="struct">neuron_t</class>
    <class kind="struct">global_neuron_params_t</class>
  </compound>
  <compound kind="file">
    <name>neuron.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>neuron_8c.html</filename>
    <includes id="neuron_8h" name="neuron.h" local="yes" imported="no">neuron.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="yes" imported="no">neuron_recording.h</includes>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" imported="no">implementations/neuron_impl.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" imported="no">plasticity/synapse_dynamics.h</includes>
    <class kind="struct">neuron_parameters</class>
    <member kind="define">
      <type>#define</type>
      <name>START_OF_GLOBAL_PARAMETERS</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a0bc6b385c441f8307f938c6c297d8d2a</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_load_neuron_parameters</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a689028531d4e9bfda09a807e264f7535</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_resume</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a2511f7541e414899ee44c6260214c6c8</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_initialise</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a4fdcd7dcb9b2ef272ba324a7ee58949f</anchor>
      <arglist>(address_t address, address_t recording_address, uint32_t *n_neurons_value, uint32_t *n_synapse_types_value, uint32_t *incoming_spike_buffer_size, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_pause</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a4ac44865a6edf62cd9e8c3349023b792</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_do_timestep_update</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ac592ab1436a441980472be8b59f54c8a</anchor>
      <arglist>(timer_t time, uint timer_count)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_add_inputs</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>abad40a95ed27eb262884dfd9f59b78d6</anchor>
      <arglist>(index_t synapse_type_index, index_t neuron_index, input_t weights_this_timestep)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_print_inputs</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a4bd09a278d3fc33a8f186f405d650c4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_print_synapse_parameters</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a243d592c67c1db595bd3e4bf73454d33</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>const char *</type>
      <name>neuron_get_synapse_type_char</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a7a4c98f25d6221625769999846e97204</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static key_t</type>
      <name>key</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ac8861193246fc34d8f29ac9d57b6791a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>use_key</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ab9132b5a04a7bdb8ac2e4293c1ec96bf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_neurons</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a7368643a28282d8b3429f0fb145aa5db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>recording_flags</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a9a97f21dc7fccaac8071bcd29894bccb</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>neuron_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>neuron_initialise</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a4fdcd7dcb9b2ef272ba324a7ee58949f</anchor>
      <arglist>(address_t address, address_t recording_address, uint32_t *n_neurons_value, uint32_t *n_synapse_types_value, uint32_t *incoming_spike_buffer_size, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_do_timestep_update</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>ac592ab1436a441980472be8b59f54c8a</anchor>
      <arglist>(timer_t time, uint timer_count)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_resume</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a2511f7541e414899ee44c6260214c6c8</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_pause</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a4ac44865a6edf62cd9e8c3349023b792</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_add_inputs</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>abad40a95ed27eb262884dfd9f59b78d6</anchor>
      <arglist>(index_t synapse_type_index, index_t neuron_index, input_t weights_this_timestep)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_print_inputs</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a4bd09a278d3fc33a8f186f405d650c4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_print_synapse_parameters</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a243d592c67c1db595bd3e4bf73454d33</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>const char *</type>
      <name>neuron_get_synapse_type_char</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a7a4c98f25d6221625769999846e97204</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_recording.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>neuron__recording_8c.html</filename>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="yes" imported="no">neuron_recording.h</includes>
    <class kind="struct">neuron_recording_header_t</class>
    <member kind="define">
      <type>#define</type>
      <name>FLOOR_TO_4</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>ac891e5a719d1f4e09038f831374b18fc</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CEIL_TO_4</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a116ca5cd8794f7ac7266ed798720a3d6</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>reset_record_counter</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a48e4d4f21167fadbe5b44ec1707677fe</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_recording_finalise</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a2c849acc5ec34882a4c75f0abbfc8cb0</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>bitfield_data_size</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>acf22d4e046f8216c065e3c77a5274f84</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_recording_read_in_elements</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>ab1ce319a9907ceeca7fa4a77029bef5c</anchor>
      <arglist>(void *recording_address, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_reset</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a6ec6bcccf5cf769f8ea0c853ab0577e9</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>allocate_word_dtcm</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a8b7a478d22db76495934d689b0a32482</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>allocate_bitfield_dtcm</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>af48d91cdeaac5c1b26bf495746757f81</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_initialise</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a9c2d66e23d2a44bedf3689e782dd0495</anchor>
      <arglist>(void *recording_address, uint32_t *recording_flags, uint32_t n_neurons, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>neuron_recording_indexes</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a7cc034f7ab8027e4b9ce66791b2365ff</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>bitfield_recording_indexes</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a2edd162fb9940477e5363386ba417f9e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>recording_info_t *</type>
      <name>recording_info</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a96a8e9a2f37a358a5264aadc6bb37263</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bitfield_info_t *</type>
      <name>bitfield_info</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a2960fd20508bd11722265c5a5e2bebec</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>recording_values</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>ac1ffd13a57545991775c1691ca0be09c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t **</type>
      <name>bitfield_values</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>ab63f6c062cd231b9b383cdf19a09dd0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>volatile uint32_t</type>
      <name>n_recordings_outstanding</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>a629e0fd3d865713eb4c4ec5c0f0c5352</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static void *</type>
      <name>reset_address</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>ac4b03f54804a47d2b1d7f9086d42292a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_recording.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>neuron__recording_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <class kind="struct">recording_values_t</class>
    <class kind="struct">bitfield_values_t</class>
    <class kind="struct">recording_info_t</class>
    <class kind="struct">bitfield_info_t</class>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_value</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a468a6544643c4df074d84a33f982f96a</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index, void *value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_accum</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a4fc5af259d7905234a9637a9daef7150</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index, accum value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_double</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ab5325e9daff0f74f70c2d6e16910e19d</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index, double value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_float</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a1f559502214e0c2e30be27aa6e6bd9ad</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index, float value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_int32</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>af70ce1643befcee0424abe320447d1de</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index, int32_t value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record_bit</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ae657cb40963f55ec96f82ae983c042e6</anchor>
      <arglist>(uint32_t var_index, uint32_t neuron_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_record</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a90e7b4bfb4eee61bc3f8162a75a03bb2</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_recording_setup_for_next_recording</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a7827a3c6f8c4ba62e3d8b15af7ae3ac0</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_reset</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a6ec6bcccf5cf769f8ea0c853ab0577e9</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_initialise</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a9c2d66e23d2a44bedf3689e782dd0495</anchor>
      <arglist>(void *recording_address, uint32_t *recording_flags, uint32_t n_neurons, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_recording_finalise</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a2c849acc5ec34882a4c75f0abbfc8cb0</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>neuron_recording_indexes</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a7cc034f7ab8027e4b9ce66791b2365ff</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>bitfield_recording_indexes</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a2edd162fb9940477e5363386ba417f9e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>recording_info_t *</type>
      <name>recording_info</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a96a8e9a2f37a358a5264aadc6bb37263</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bitfield_info_t *</type>
      <name>bitfield_info</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a2960fd20508bd11722265c5a5e2bebec</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint8_t **</type>
      <name>recording_values</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ac1ffd13a57545991775c1691ca0be09c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t **</type>
      <name>bitfield_values</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ab63f6c062cd231b9b383cdf19a09dd0d</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>maths.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/</path>
    <filename>maths_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <class kind="struct">int16_lut</class>
    <member kind="define">
      <type>#define</type>
      <name>MIN</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>ad2f3678bf5eae3684fc497130b946eae</anchor>
      <arglist>(X, Y)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MAX</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>aff9931d7524c88e07743af6535b20761</anchor>
      <arglist>(X, Y)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int16_lut *</type>
      <name>maths_copy_int16_lut</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a510f113b80d885ec2b2e8b80d8cd08b6</anchor>
      <arglist>(address_t *address)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>maths_lut_exponential_decay</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a7c315224937c5fa8f619c4ed6be5c89d</anchor>
      <arglist>(uint32_t time, const int16_lut *lut)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>maths_clamp_pot</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a260ef4f2441756ae0507deceefda7460</anchor>
      <arglist>(int32_t x, uint32_t shift)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>maths_mul_16x16</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a470b9772ae34f0a79199154330378c7f</anchor>
      <arglist>(int16_t x, int16_t y)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>maths_fixed_mul16</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a684f0b41c83b59209f8ee616a57474ec</anchor>
      <arglist>(int32_t a, int32_t b, const int32_t fixed_point_position)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>maths_fixed_mul32</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a9570356b9b13ddd638685b38b66ed6ff</anchor>
      <arglist>(int32_t a, int32_t b, const int32_t fixed_point_position)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>post_events.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/</path>
    <filename>post__events_8h.html</filename>
    <class kind="struct">post_event_history_t</class>
    <class kind="struct">post_event_window_t</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_POST_SYNAPTIC_EVENTS</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a3e545bee7f8f0a5c41ff9fe6a0536604</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_event_history</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a6deeebe9df2c90b608869bd1934af9db</anchor>
      <arglist>(const post_event_history_t *events)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_history_t *</type>
      <name>post_events_init_buffers</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a508c0da58071b296cc6bac46cba48f5a</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_window_t</type>
      <name>post_events_get_window_delayed</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>ac8fb2d0d29c873fd49869b215d81b60d</anchor>
      <arglist>(const post_event_history_t *events, uint32_t begin_time, uint32_t end_time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_window_t</type>
      <name>post_events_next</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a8b3f1431b102ab55a162d23e637d1a2f</anchor>
      <arglist>(post_event_window_t window)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>post_events_add</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>ac02b9cbe20e4e44d571b0d80968634ef</anchor>
      <arglist>(uint32_t time, post_event_history_t *events, post_trace_t trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_delayed_window_events</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>ae8696ad6309cecd361c85e5c35bc4aab</anchor>
      <arglist>(const post_event_history_t *post_event_history, uint32_t begin_time, uint32_t end_time, uint32_t delay_dendritic)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>stdp_typedefs.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/</path>
    <filename>stdp__typedefs_8h.html</filename>
    <member kind="define">
      <type>#define</type>
      <name>STDP_FIXED_POINT</name>
      <anchorfile>stdp__typedefs_8h.html</anchorfile>
      <anchor>ad2fac83f5bb9b0f79f346200d9f74024</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>STDP_FIXED_POINT_ONE</name>
      <anchorfile>stdp__typedefs_8h.html</anchorfile>
      <anchor>aa17e993cea62822ef342b0db7ed156f5</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>STDP_FIXED_MUL_16X16</name>
      <anchorfile>stdp__typedefs_8h.html</anchorfile>
      <anchor>aadb4d7a82820e2de3f998e902b7cd87a</anchor>
      <arglist>(a, b)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_stdp_mad_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/</path>
    <filename>synapse__dynamics__stdp__mad__impl_8c.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="no" imported="no">neuron/synapses.h</includes>
    <includes id="maths_8h" name="maths.h" local="yes" imported="no">maths.h</includes>
    <includes id="post__events_8h" name="post_events.h" local="yes" imported="no">post_events.h</includes>
    <includes id="weight_8h" name="weight.h" local="yes" imported="no">weight_dependence/weight.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing_dependence/timing.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="no" imported="no">neuron/plasticity/synapse_dynamics.h</includes>
    <class kind="struct">stdp_params</class>
    <class kind="struct">pre_event_history_t</class>
    <class kind="struct">synapse_row_plastic_data_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_AXONAL_DELAY_BITS</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ad56063ded3be48fa1e95ab2237e70bf4</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_AXONAL_DELAY_MASK</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a7ef4633ab4f3f1be7e55dfedc08f8405</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>plasticity_update_synapse</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>aa195e42fb2e365fe51384e2ef8a95ec8</anchor>
      <arglist>(const uint32_t time, const uint32_t last_pre_time, const pre_trace_t last_pre_trace, const pre_trace_t new_pre_trace, const uint32_t delay_dendritic, const uint32_t delay_axonal, update_state_t current_state, const post_event_history_t *post_event_history)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_print_plastic_synapses</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ac0dc7f1b3f6348db279fbad8c8040b1c</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>sparse_axonal_delay</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>abade6b73a469c1ff0e54366f065343e5</anchor>
      <arglist>(uint32_t x)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>af8856a6cc26be71631d24fc5eec3846e</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_address, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>input_t</type>
      <name>synapse_dynamics_get_intrinsic_bias</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a06ce5830924c098a9668b25c9f09c7cc</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a24b755e1d96fcab4e950b83796376e75</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a540b2206e6909e8e88c3a98a47ddcb2a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_find_neuron</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a5893fd33bdac3b991ecb7cb61feb4188</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay, uint32_t *offset, uint32_t *synapse_type)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_remove_neuron</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>af3e517401d329d33f14b0ba70743e127</anchor>
      <arglist>(uint32_t offset, synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static control_t</type>
      <name>control_conversion</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a06f2e2d805f0d8aa8b3ca7b687f24a24</anchor>
      <arglist>(uint32_t id, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_add_neuron</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ac877b6394f131f1944a720c387af6ac1</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t weight, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_n_connections_in_row</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>aca5fc1011c991013823ad76158bf57f3</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_mask</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a84db6c41c7cf03558016d477d8df4d37</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_index_mask</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ac3299a10c6a78f6e4f37246ab79a0736</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_delay_index_type_bits</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a6ee98912aaae99284ae103901c4a6879</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_mask</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>af786c2a0c6f40c688029991d5b9711a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static stdp_params</type>
      <name>params</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a159669347528cd4f88c368d0d33e4670</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>num_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a9e7456ba7de4fa401d09c84644229f91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a865d0cf426d384be02e8f07b34b05e31</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>post_event_history_t *</type>
      <name>post_event_history</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a9738c22cad44349036699b2383355540</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight.h</includes>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>synapse_structure_get_update_state</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>a7d9484a9e3bcbe6f1beea90d958b93f2</anchor>
      <arglist>(plastic_synapse_t synaptic_word, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>synapse_structure_get_final_state</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>ae90f5f94b04793a935e8daf9490b0806</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_final_weight</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>abf18bb0d3b4ca4464892e6f5631fd455</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_get_final_synaptic_word</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>a37a088e619407ca72cc01a1c19d54fda</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_create_synapse</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>a7d6d84bcbbb6e0a39a6e880d665c0511</anchor>
      <arglist>(weight_t weight)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_weight</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>aead91a129a9df6e8dfcae25ef764e7af</anchor>
      <arglist>(plastic_synapse_t synaptic_word)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure_weight_accumulator_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__accumulator__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" imported="no">synapse_structure.h</includes>
    <class kind="struct">plastic_synapse_t</class>
    <class kind="struct">update_state_t</class>
    <member kind="typedef">
      <type>plastic_synapse_t</type>
      <name>final_state_t</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>a174a20aa9aac3b4c8ecda186d8db0083</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>synapse_structure_get_update_state</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>a7d9484a9e3bcbe6f1beea90d958b93f2</anchor>
      <arglist>(plastic_synapse_t synaptic_word, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>synapse_structure_get_final_state</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>ae90f5f94b04793a935e8daf9490b0806</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_final_weight</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>abf18bb0d3b4ca4464892e6f5631fd455</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_get_final_synaptic_word</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>a37a088e619407ca72cc01a1c19d54fda</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_create_synapse</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>a7d6d84bcbbb6e0a39a6e880d665c0511</anchor>
      <arglist>(weight_t weight)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_weight</name>
      <anchorfile>synapse__structure__weight__accumulator__impl_8h.html</anchorfile>
      <anchor>aead91a129a9df6e8dfcae25ef764e7af</anchor>
      <arglist>(plastic_synapse_t synaptic_word)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure_weight_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__impl_8h.html</filename>
    <member kind="typedef">
      <type>weight_t</type>
      <name>plastic_synapse_t</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>ac4517cb4731427f27418fdf8107fa8c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>weight_state_t</type>
      <name>update_state_t</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>ac4fd00ce43d4ad3f6181dde377224723</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>weight_t</type>
      <name>final_state_t</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>a3f28e6a9e3f4b037ca7cd80997a3506d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>synapse_structure_get_update_state</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>a7d9484a9e3bcbe6f1beea90d958b93f2</anchor>
      <arglist>(plastic_synapse_t synaptic_word, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>synapse_structure_get_final_state</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>ae90f5f94b04793a935e8daf9490b0806</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_final_weight</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>abf18bb0d3b4ca4464892e6f5631fd455</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_get_final_synaptic_word</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>a37a088e619407ca72cc01a1c19d54fda</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_create_synapse</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>a7d6d84bcbbb6e0a39a6e880d665c0511</anchor>
      <arglist>(weight_t weight)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_weight</name>
      <anchorfile>synapse__structure__weight__impl_8h.html</anchorfile>
      <anchor>aead91a129a9df6e8dfcae25ef764e7af</anchor>
      <arglist>(plastic_synapse_t synaptic_word)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure_weight_state_accumulator_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__state__accumulator__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" imported="no">synapse_structure.h</includes>
    <class kind="struct">plastic_synapse_t</class>
    <class kind="struct">update_state_t</class>
    <member kind="typedef">
      <type>plastic_synapse_t</type>
      <name>final_state_t</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>a174a20aa9aac3b4c8ecda186d8db0083</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>synapse_structure_get_update_state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>a7d9484a9e3bcbe6f1beea90d958b93f2</anchor>
      <arglist>(plastic_synapse_t synaptic_word, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>synapse_structure_get_final_state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>ae90f5f94b04793a935e8daf9490b0806</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_final_weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>abf18bb0d3b4ca4464892e6f5631fd455</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_get_final_synaptic_word</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>a37a088e619407ca72cc01a1c19d54fda</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_create_synapse</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>a7d6d84bcbbb6e0a39a6e880d665c0511</anchor>
      <arglist>(weight_t weight)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__impl_8h.html</anchorfile>
      <anchor>aead91a129a9df6e8dfcae25ef764e7af</anchor>
      <arglist>(plastic_synapse_t synaptic_word)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure_weight_state_accumulator_window_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__state__accumulator__window__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" imported="no">synapse_structure.h</includes>
    <class kind="struct">plastic_synapse_t</class>
    <class kind="struct">update_state_t</class>
    <member kind="typedef">
      <type>plastic_synapse_t</type>
      <name>final_state_t</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a174a20aa9aac3b4c8ecda186d8db0083</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>synapse_structure_get_update_state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a7d9484a9e3bcbe6f1beea90d958b93f2</anchor>
      <arglist>(plastic_synapse_t synaptic_word, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>synapse_structure_get_final_state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>ae90f5f94b04793a935e8daf9490b0806</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_final_weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>abf18bb0d3b4ca4464892e6f5631fd455</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_get_final_synaptic_word</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a37a088e619407ca72cc01a1c19d54fda</anchor>
      <arglist>(final_state_t final_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static plastic_synapse_t</type>
      <name>synapse_structure_create_synapse</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a7d6d84bcbbb6e0a39a6e880d665c0511</anchor>
      <arglist>(weight_t weight)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_structure_get_weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>aead91a129a9df6e8dfcae25ef764e7af</anchor>
      <arglist>(plastic_synapse_t synaptic_word)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>random_util.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>random__util_8h.html</filename>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>mars_kiss_fixed_point</name>
      <anchorfile>random__util_8h.html</anchorfile>
      <anchor>a888c74ee81620d84c956eed32713f074</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure.h</includes>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_nearest_pair_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__nearest__pair__impl_8c.html</filename>
    <includes id="timing__nearest__pair__impl_8h" name="timing_nearest_pair_impl.h" local="yes" imported="no">timing_nearest_pair_impl.h</includes>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing__nearest__pair__impl_8c.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_plus_lookup</name>
      <anchorfile>timing__nearest__pair__impl_8c.html</anchorfile>
      <anchor>ac2082ebe7d3d3c59956cbdca4cf3208c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_minus_lookup</name>
      <anchorfile>timing__nearest__pair__impl_8c.html</anchorfile>
      <anchor>a5df0802a6397901234e922aff1e58843</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_nearest_pair_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__nearest__pair__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <class kind="struct">post_trace_t</class>
    <class kind="struct">pre_trace_t</class>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__nearest__pair__impl_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__nearest__pair__impl_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__nearest__pair__impl_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__nearest__pair__impl_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__nearest__pair__impl_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_pair_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pair__impl_8c.html</filename>
    <includes id="timing__pair__impl_8h" name="timing_pair_impl.h" local="yes" imported="no">timing_pair_impl.h</includes>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing__pair__impl_8c.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_plus_lookup</name>
      <anchorfile>timing__pair__impl_8c.html</anchorfile>
      <anchor>ac2082ebe7d3d3c59956cbdca4cf3208c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_minus_lookup</name>
      <anchorfile>timing__pair__impl_8c.html</anchorfile>
      <anchor>a5df0802a6397901234e922aff1e58843</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_pair_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pair__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <member kind="typedef">
      <type>int16_t</type>
      <name>post_trace_t</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a69a9eeb52cef62afc1ac54cdd56c3aa5</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>int16_t</type>
      <name>pre_trace_t</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a92311408eb25d9fb4071ad29aa1f9372</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__pair__impl_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_pfister_triplet_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pfister__triplet__impl_8c.html</filename>
    <includes id="timing__pfister__triplet__impl_8h" name="timing_pfister_triplet_impl.h" local="yes" imported="no">timing_pfister_triplet_impl.h</includes>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing__pfister__triplet__impl_8c.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_plus_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8c.html</anchorfile>
      <anchor>ac2082ebe7d3d3c59956cbdca4cf3208c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_minus_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8c.html</anchorfile>
      <anchor>a5df0802a6397901234e922aff1e58843</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_x_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8c.html</anchorfile>
      <anchor>a1dfad00a19d11bc65778f6267d41d281</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_y_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8c.html</anchorfile>
      <anchor>ad7ec865b94cae52580b7e7d51b408ab9</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_pfister_triplet_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pfister__triplet__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__two__term_8h" name="weight_two_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_two_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <class kind="struct">post_trace_t</class>
    <class kind="struct">pre_trace_t</class>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_plus_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>ac2082ebe7d3d3c59956cbdca4cf3208c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_minus_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a5df0802a6397901234e922aff1e58843</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_x_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>a1dfad00a19d11bc65778f6267d41d281</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_y_lookup</name>
      <anchorfile>timing__pfister__triplet__impl_8h.html</anchorfile>
      <anchor>ad7ec865b94cae52580b7e7d51b408ab9</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_recurrent_common.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__common_8h.html</filename>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="random__util_8h" name="random_util.h" local="yes" imported="no">random_util.h</includes>
    <member kind="enumeration">
      <type></type>
      <name>recurrent_state_machine_state_t</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>aa582d447f01913259d0486c7335a3455</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_IDLE</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>aa582d447f01913259d0486c7335a3455aaade5e53e88cf231292cd1142cce2afe</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_PRE_OPEN</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>aa582d447f01913259d0486c7335a3455acaed6c3d35a93a30b38bdf72f2d13b7e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_POST_OPEN</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>aa582d447f01913259d0486c7335a3455a166a47bbf11a3281b3fd852f670dbb57</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>timing_recurrent_in_pre_window</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a90a8775ed6377892cbe3e6fe3486ac60</anchor>
      <arglist>(uint32_t time_since_last_event, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>timing_recurrent_in_post_window</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>af319d78dba6183bf12bbfe67cf64d94b</anchor>
      <arglist>(uint32_t time_since_last_event, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_recurrent_calculate_pre_window</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a6fe02a9d920395cd33c00af313a22386</anchor>
      <arglist>(update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_recurrent_calculate_post_window</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a55166b85b53fca83e96b96f206cc168a</anchor>
      <arglist>(update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__recurrent__common_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_recurrent_dual_fsm_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__dual__fsm__impl_8c.html</filename>
    <includes id="timing__recurrent__dual__fsm__impl_8h" name="timing_recurrent_dual_fsm_impl.h" local="yes" imported="no">timing_recurrent_dual_fsm_impl.h</includes>
    <class kind="struct">dual_fsm_config_t</class>
    <member kind="function">
      <type>uint32_t *</type>
      <name>timing_initialise</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8c.html</anchorfile>
      <anchor>a5a9c0d92e3c55aa3c23c1fb2e1ff61bc</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>pre_exp_dist_lookup</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8c.html</anchorfile>
      <anchor>a81f99d89b60b27293823f709ead9c577</anchor>
      <arglist>[STDP_FIXED_POINT_ONE]</arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>post_exp_dist_lookup</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8c.html</anchorfile>
      <anchor>ac94444391be2832f0c77cec022b96584</anchor>
      <arglist>[STDP_FIXED_POINT_ONE]</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_trace_region_data_t</type>
      <name>plasticity_trace_region_data</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8c.html</anchorfile>
      <anchor>aa00b23ef207940abda557ff4899420c0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_recurrent_dual_fsm_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__dual__fsm__impl_8h.html</filename>
    <includes id="synapse__structure__weight__accumulator__impl_8h" name="synapse_structure_weight_accumulator_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="random__util_8h" name="random_util.h" local="yes" imported="no">random_util.h</includes>
    <class kind="struct">plasticity_trace_region_data_t</class>
    <member kind="typedef">
      <type>uint16_t</type>
      <name>post_trace_t</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>a9621a91ad163bd8c6a1ad333789e500a</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>uint16_t</type>
      <name>pre_trace_t</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>af2237657ec5c022902e4d5fc7e7dad69</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_trace_region_data_t</type>
      <name>plasticity_trace_region_data</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8h.html</anchorfile>
      <anchor>aa00b23ef207940abda557ff4899420c0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_recurrent_pre_stochastic_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__pre__stochastic__impl_8c.html</filename>
    <includes id="timing__recurrent__pre__stochastic__impl_8h" name="timing_recurrent_pre_stochastic_impl.h" local="yes" imported="no">timing_recurrent_pre_stochastic_impl.h</includes>
    <class kind="struct">pre_stochastic_config_t</class>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8c.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>pre_exp_dist_lookup</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8c.html</anchorfile>
      <anchor>a81f99d89b60b27293823f709ead9c577</anchor>
      <arglist>[STDP_FIXED_POINT_ONE]</arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>post_exp_dist_lookup</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8c.html</anchorfile>
      <anchor>ac94444391be2832f0c77cec022b96584</anchor>
      <arglist>[STDP_FIXED_POINT_ONE]</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_trace_region_data_t</type>
      <name>plasticity_trace_region_data</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8c.html</anchorfile>
      <anchor>aa00b23ef207940abda557ff4899420c0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_recurrent_pre_stochastic_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__pre__stochastic__impl_8h.html</filename>
    <includes id="synapse__structure__weight__state__accumulator__window__impl_8h" name="synapse_structure_weight_state_accumulator_window_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_state_accumulator_window_impl.h</includes>
    <includes id="timing__recurrent__common_8h" name="timing_recurrent_common.h" local="yes" imported="no">timing_recurrent_common.h</includes>
    <class kind="struct">post_trace_t</class>
    <class kind="struct">pre_trace_t</class>
    <class kind="struct">plasticity_trace_region_data_t</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>timing_recurrent_in_pre_window</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8h.html</anchorfile>
      <anchor>a90a8775ed6377892cbe3e6fe3486ac60</anchor>
      <arglist>(uint32_t time_since_last_event, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>timing_recurrent_in_post_window</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8h.html</anchorfile>
      <anchor>af319d78dba6183bf12bbfe67cf64d94b</anchor>
      <arglist>(uint32_t time_since_last_event, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_recurrent_calculate_pre_window</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8h.html</anchorfile>
      <anchor>a6fe02a9d920395cd33c00af313a22386</anchor>
      <arglist>(update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_recurrent_calculate_post_window</name>
      <anchorfile>timing__recurrent__pre__stochastic__impl_8h.html</anchorfile>
      <anchor>a55166b85b53fca83e96b96f206cc168a</anchor>
      <arglist>(update_state_t previous_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_vogels_2011_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__vogels__2011__impl_8c.html</filename>
    <includes id="timing__vogels__2011__impl_8h" name="timing_vogels_2011_impl.h" local="yes" imported="no">timing_vogels_2011_impl.h</includes>
    <class kind="struct">vogels_2011_config_t</class>
    <member kind="function">
      <type>address_t</type>
      <name>timing_initialise</name>
      <anchorfile>timing__vogels__2011__impl_8c.html</anchorfile>
      <anchor>adcf80560bde3d552d7ef273645c530fa</anchor>
      <arglist>(address_t address)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_lookup</name>
      <anchorfile>timing__vogels__2011__impl_8c.html</anchorfile>
      <anchor>af6ff5d053eae1db7ea80f598852073c4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>plasticity_trace_region_data_t</type>
      <name>plasticity_trace_region_data</name>
      <anchorfile>timing__vogels__2011__impl_8c.html</anchorfile>
      <anchor>aa00b23ef207940abda557ff4899420c0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing_vogels_2011_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__vogels__2011__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" imported="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" imported="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" imported="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <class kind="struct">plasticity_trace_region_data_t</class>
    <member kind="typedef">
      <type>int16_t</type>
      <name>post_trace_t</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a69a9eeb52cef62afc1ac54cdd56c3aa5</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>int16_t</type>
      <name>pre_trace_t</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a92311408eb25d9fb4071ad29aa1f9372</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int16_t</type>
      <name>timing_add_spike</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a46811ff7207ae7a5ecb524664cd51445</anchor>
      <arglist>(uint32_t time, uint32_t last_time, int16_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_get_initial_post_trace</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>aa7468f2d715d29ef38d1b362be47c5c1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_trace_t</type>
      <name>timing_add_post_spike</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a02c46ae67288b70c15e59dac89a00046</anchor>
      <arglist>(uint32_t time, uint32_t last_time, post_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static pre_trace_t</type>
      <name>timing_add_pre_spike</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a530f515f7e15cce9bbd8e156b03955fa</anchor>
      <arglist>(uint32_t time, uint32_t last_time, pre_trace_t last_trace)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_pre_spike</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a3f39ea9a044424ed7c54b5306da34765</anchor>
      <arglist>(uint32_t time, pre_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static update_state_t</type>
      <name>timing_apply_post_spike</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a9427624dd6fcaf52cddc8d1ec0b24dda</anchor>
      <arglist>(uint32_t time, post_trace_t trace, uint32_t last_pre_time, pre_trace_t last_pre_trace, uint32_t last_post_time, post_trace_t last_post_trace, update_state_t previous_state)</arglist>
    </member>
    <member kind="variable">
      <type>int16_lut *</type>
      <name>tau_lookup</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>af6ff5d053eae1db7ea80f598852073c4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <member kind="function">
      <type>address_t</type>
      <name>weight_initialise</name>
      <anchorfile>weight_8h.html</anchorfile>
      <anchor>a499ff9e19e3982f41bd7422fafebca2e</anchor>
      <arglist>(address_t address, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_get_initial</name>
      <anchorfile>weight_8h.html</anchorfile>
      <anchor>a77fd3764c1b7b7c67822db6da73f73f5</anchor>
      <arglist>(weight_t weight, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>weight_get_final</name>
      <anchorfile>weight_8h.html</anchorfile>
      <anchor>a5321486a75826401b258999334c52640</anchor>
      <arglist>(weight_state_t new_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_one_term_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__one__term__impl_8c.html</filename>
    <includes id="weight__additive__one__term__impl_8h" name="weight_additive_one_term_impl.h" local="yes" imported="no">weight_additive_one_term_impl.h</includes>
    <class kind="struct">additive_one_term_config_t</class>
    <member kind="function">
      <type>address_t</type>
      <name>weight_initialise</name>
      <anchorfile>weight__additive__one__term__impl_8c.html</anchorfile>
      <anchor>a499ff9e19e3982f41bd7422fafebca2e</anchor>
      <arglist>(address_t address, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_weight_region_data_t *</type>
      <name>plasticity_weight_region_data</name>
      <anchorfile>weight__additive__one__term__impl_8c.html</anchorfile>
      <anchor>aff9620807595c2091e6bd5887da64f5b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_one_term_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__one__term__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="yes" imported="no">weight_one_term.h</includes>
    <class kind="struct">plasticity_weight_region_data_t</class>
    <class kind="struct">weight_state_t</class>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_get_initial</name>
      <anchorfile>weight__additive__one__term__impl_8h.html</anchorfile>
      <anchor>a77fd3764c1b7b7c67822db6da73f73f5</anchor>
      <arglist>(weight_t weight, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_depression</name>
      <anchorfile>weight__additive__one__term__impl_8h.html</anchorfile>
      <anchor>a8d5d7cd244ca1fea66a9f4943f8586e2</anchor>
      <arglist>(weight_state_t state, int32_t a2_minus)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_potentiation</name>
      <anchorfile>weight__additive__one__term__impl_8h.html</anchorfile>
      <anchor>a901c079ce70b3191420d6eb68d5cb63e</anchor>
      <arglist>(weight_state_t state, int32_t a2_plus)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>weight_get_final</name>
      <anchorfile>weight__additive__one__term__impl_8h.html</anchorfile>
      <anchor>a5321486a75826401b258999334c52640</anchor>
      <arglist>(weight_state_t new_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_two_term_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__two__term__impl_8c.html</filename>
    <includes id="weight__additive__two__term__impl_8h" name="weight_additive_two_term_impl.h" local="yes" imported="no">weight_additive_two_term_impl.h</includes>
    <class kind="struct">additive_two_term_config_t</class>
    <member kind="function">
      <type>address_t</type>
      <name>weight_initialise</name>
      <anchorfile>weight__additive__two__term__impl_8c.html</anchorfile>
      <anchor>a499ff9e19e3982f41bd7422fafebca2e</anchor>
      <arglist>(address_t address, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_weight_region_data_t *</type>
      <name>plasticity_weight_region_data</name>
      <anchorfile>weight__additive__two__term__impl_8c.html</anchorfile>
      <anchor>aff9620807595c2091e6bd5887da64f5b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_two_term_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__two__term__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <includes id="weight__two__term_8h" name="weight_two_term.h" local="yes" imported="no">weight_two_term.h</includes>
    <class kind="struct">plasticity_weight_region_data_t</class>
    <class kind="struct">weight_state_t</class>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_get_initial</name>
      <anchorfile>weight__additive__two__term__impl_8h.html</anchorfile>
      <anchor>a77fd3764c1b7b7c67822db6da73f73f5</anchor>
      <arglist>(weight_t weight, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_two_term_apply_depression</name>
      <anchorfile>weight__additive__two__term__impl_8h.html</anchorfile>
      <anchor>a847604ae6bf74d6d0605d660287fa3a1</anchor>
      <arglist>(weight_state_t state, int32_t a2_minus, int32_t a3_minus)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_two_term_apply_potentiation</name>
      <anchorfile>weight__additive__two__term__impl_8h.html</anchorfile>
      <anchor>aa995e821053917cb970fffd095992073</anchor>
      <arglist>(weight_state_t state, int32_t a2_plus, int32_t a3_plus)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>weight_get_final</name>
      <anchorfile>weight__additive__two__term__impl_8h.html</anchorfile>
      <anchor>a5321486a75826401b258999334c52640</anchor>
      <arglist>(weight_state_t new_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_multiplicative_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__multiplicative__impl_8c.html</filename>
    <includes id="weight__multiplicative__impl_8h" name="weight_multiplicative_impl.h" local="yes" imported="no">weight_multiplicative_impl.h</includes>
    <class kind="struct">multiplicative_config_t</class>
    <member kind="function">
      <type>address_t</type>
      <name>weight_initialise</name>
      <anchorfile>weight__multiplicative__impl_8c.html</anchorfile>
      <anchor>a499ff9e19e3982f41bd7422fafebca2e</anchor>
      <arglist>(address_t address, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="variable">
      <type>plasticity_weight_region_data_t *</type>
      <name>plasticity_weight_region_data</name>
      <anchorfile>weight__multiplicative__impl_8c.html</anchorfile>
      <anchor>aff9620807595c2091e6bd5887da64f5b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>weight_multiply_right_shift</name>
      <anchorfile>weight__multiplicative__impl_8c.html</anchorfile>
      <anchor>a04481d5906cf9a60cb1b2c2c1e68de54</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_multiplicative_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__multiplicative__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" imported="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" imported="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="yes" imported="no">weight_one_term.h</includes>
    <class kind="struct">plasticity_weight_region_data_t</class>
    <class kind="struct">weight_state_t</class>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_get_initial</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a77fd3764c1b7b7c67822db6da73f73f5</anchor>
      <arglist>(weight_t weight, index_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_depression</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>abd21eca2990446a700a7b4ee6fcfaa7f</anchor>
      <arglist>(weight_state_t state, int32_t depression)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_potentiation</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a09f2d7b47e533a84ab8ba0e032293358</anchor>
      <arglist>(weight_state_t state, int32_t potentiation)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>weight_get_final</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a5321486a75826401b258999334c52640</anchor>
      <arglist>(weight_state_t new_state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_one_term.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__one__term_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="yes" imported="no">weight.h</includes>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_depression</name>
      <anchorfile>weight__one__term_8h.html</anchorfile>
      <anchor>abd21eca2990446a700a7b4ee6fcfaa7f</anchor>
      <arglist>(weight_state_t state, int32_t depression)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_one_term_apply_potentiation</name>
      <anchorfile>weight__one__term_8h.html</anchorfile>
      <anchor>a09f2d7b47e533a84ab8ba0e032293358</anchor>
      <arglist>(weight_state_t state, int32_t potentiation)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_two_term.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__two__term_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="yes" imported="no">weight.h</includes>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_two_term_apply_depression</name>
      <anchorfile>weight__two__term_8h.html</anchorfile>
      <anchor>a81774c4ad183624acb0f1347fcaf7af6</anchor>
      <arglist>(weight_state_t state, int32_t depression_1, int32_t depression_2)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_state_t</type>
      <name>weight_two_term_apply_potentiation</name>
      <anchorfile>weight__two__term_8h.html</anchorfile>
      <anchor>a35fc7bcf56c4a7b08d1d24f456797eec</anchor>
      <arglist>(weight_state_t state, int32_t potentiation_1, int32_t potentiation_2)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/</path>
    <filename>synapse__dynamics_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a60af161f5a3ec5b77f236d4a5d6c2742</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>input_t</type>
      <name>synapse_dynamics_get_intrinsic_bias</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a06ce5830924c098a9668b25c9f09c7cc</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_print_plastic_synapses</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>ac0dc7f1b3f6348db279fbad8c8040b1c</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a24b755e1d96fcab4e950b83796376e75</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_saturation_count</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a540b2206e6909e8e88c3a98a47ddcb2a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_find_neuron</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a5893fd33bdac3b991ecb7cb61feb4188</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay, uint32_t *offset, uint32_t *synapse_type)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_remove_neuron</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>af3e517401d329d33f14b0ba70743e127</anchor>
      <arglist>(uint32_t offset, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_add_neuron</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>ac877b6394f131f1944a720c387af6ac1</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t weight, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_n_connections_in_row</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>aca5fc1011c991013823ad76158bf57f3</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_static_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/plasticity/</path>
    <filename>synapse__dynamics__static__impl_8c.html</filename>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" imported="no">synapse_dynamics.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>aed92420010ba63593b139d59263ee80e</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffer, uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>input_t</type>
      <name>synapse_dynamics_get_intrinsic_bias</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a06ce5830924c098a9668b25c9f09c7cc</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_print_plastic_synapses</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>acb203e3c4f9b3e72bb69ce5033e83543</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, uint32_t *ring_buffer_to_input_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a24b755e1d96fcab4e950b83796376e75</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a540b2206e6909e8e88c3a98a47ddcb2a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_find_neuron</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a5893fd33bdac3b991ecb7cb61feb4188</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay, uint32_t *offset, uint32_t *synapse_type)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_remove_neuron</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>af3e517401d329d33f14b0ba70743e127</anchor>
      <arglist>(uint32_t offset, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_add_neuron</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>ac877b6394f131f1944a720c387af6ac1</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t weight, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_n_connections_in_row</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>aca5fc1011c991013823ad76158bf57f3</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_mask</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a84db6c41c7cf03558016d477d8df4d37</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>af20079aa1e3c31a3efd344176025ce0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_mask</name>
      <anchorfile>synapse__dynamics__static__impl_8c.html</anchorfile>
      <anchor>af786c2a0c6f40c688029991d5b9711a7</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>population_table.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/population_table/</path>
    <filename>population__table_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a5f92af4dd47e65504cbbbcb265083196</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, address_t direct_rows_address, uint32_t *row_max_n_words)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_load_bitfields</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a4e78f94389fe12981acf2cea7e8bfe91</anchor>
      <arglist>(filter_region_t *filter_region)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_first_address</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a511a4004e5621e6ec83228d4e4f94672</anchor>
      <arglist>(spike_t spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a06008941811a064b8c67dcf3a5846cde</anchor>
      <arglist>(spike_t *spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>ghost_pop_table_searches</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ac69edc9d8d10785e6775d3805c8e7037</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>invalid_master_pop_hits</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a40086bc81cde7081da9ed9b52b6bfaff</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>failed_bit_field_reads</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a3fe8cdf904112ab379545b0d8f7a5d20</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>bit_field_filtered_packets</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a442bf46f572f3fc97a52421b7e1a0f87</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>population_table_binary_search_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/population_table/</path>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <includes id="population__table_8h" name="population_table.h" local="yes" imported="no">population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <class kind="struct">master_population_table_entry</class>
    <class kind="struct">extra_info</class>
    <class kind="struct">address_and_row_length</class>
    <class kind="union">address_list_entry</class>
    <class kind="struct">pop_table_config_t</class>
    <member kind="define">
      <type>#define</type>
      <name>BITS_PER_WORD</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>af859a98f57110e5243e8f0541319e43b</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>TOP_BIT_IN_WORD</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a76abab9c83287abfbdde2324b659b836</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NOT_IN_MASTER_POP_TABLE_FLAG</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5f369817d958cb4c367752b5558957b1</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>N_ADDRESS_BITS</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a2233d5046582aeea3564c6ec3e72c553</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>INDIRECT_ADDRESS_SHIFT</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a36896ff3554f8b8ee7fe1599ec6c26f5</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_direct_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0f6729803ce65a621db8be58bfa1d972</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_offset</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a30c2c744e7524091a4a2b64d231fdf4f</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>aa48b23a2a333284836c0054f7113ca95</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_row_length</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a90850a3d006b876ba62076c80a401be1</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_index</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>abbbbe3092321f99b294c4143a2438c5e</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_sum</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5d4827066ef5e80065b7008054bd7686</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_bitfield_sum</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a4dab389e388857fd430ade234d606239</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_neuron_id</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab08d6807fc8fd46ed5f70a8bd14a5a93</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_local_neuron_id</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0e1b8eb97598151a700431dc6226d089</anchor>
      <arglist>(master_population_table_entry entry, extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_master_population_table</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a3c2c10dcc54c9ec95a730e4c1324a2c5</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>matches</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a84c16f8e8fdf9909791cbca87e983dde</anchor>
      <arglist>(uint32_t mp_i, uint32_t key)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_bitfields</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab9711943341e2f63e48945e4dfee5099</anchor>
      <arglist>(uint32_t mp_i, uint32_t start, uint32_t end, filter_info_t *filters)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_load_bitfields</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a4e78f94389fe12981acf2cea7e8bfe91</anchor>
      <arglist>(filter_region_t *filter_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>population_table_position_in_the_master_pop_array</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab4759e505b101d5eb919685e2bfb55b0</anchor>
      <arglist>(spike_t spike, uint32_t *position)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5f92af4dd47e65504cbbbcb265083196</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, address_t direct_rows_address, uint32_t *row_max_n_words)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_first_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a511a4004e5621e6ec83228d4e4f94672</anchor>
      <arglist>(spike_t spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a06008941811a064b8c67dcf3a5846cde</anchor>
      <arglist>(spike_t *spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static master_population_table_entry *</type>
      <name>master_population_table</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a165c9820d20b3f9cce795f65e326708b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>master_population_table_length</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac791e8f016a5422c047f964641706f42</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static address_list_entry *</type>
      <name>address_list</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a7dca3eb9efb99180a67a18d70e3e7e0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synaptic_rows_base_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a3808a62ff90d026b89ca198c9a503295</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>direct_rows_base_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a53f683b47d1883d1fe9dc988c1b6a101</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static spike_t</type>
      <name>last_spike</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>af5f8c1b781901d417e09126b75d60140</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>last_neuron_id</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac37238a52469aa0b4303c54e119a6dce</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t</type>
      <name>next_item</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1002add104ecafe843ef47eadf096e0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t</type>
      <name>items_to_go</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>aebd5b17aab1bbe44fa564e8786f84d94</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bit_field_t *</type>
      <name>connectivity_bit_field</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>af5132d7f50c964c1994dcefe0a008a88</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>ghost_pop_table_searches</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac69edc9d8d10785e6775d3805c8e7037</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>invalid_master_pop_hits</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a40086bc81cde7081da9ed9b52b6bfaff</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>failed_bit_field_reads</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a3fe8cdf904112ab379545b0d8f7a5d20</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>bit_field_filtered_packets</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a442bf46f572f3fc97a52421b7e1a0f87</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_direct_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0f6729803ce65a621db8be58bfa1d972</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_offset</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a30c2c744e7524091a4a2b64d231fdf4f</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>aa48b23a2a333284836c0054f7113ca95</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_row_length</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a90850a3d006b876ba62076c80a401be1</anchor>
      <arglist>(address_and_row_length entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_index</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>abbbbe3092321f99b294c4143a2438c5e</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_sum</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5d4827066ef5e80065b7008054bd7686</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_bitfield_sum</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a4dab389e388857fd430ade234d606239</anchor>
      <arglist>(extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_neuron_id</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab08d6807fc8fd46ed5f70a8bd14a5a93</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_local_neuron_id</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0e1b8eb97598151a700431dc6226d089</anchor>
      <arglist>(master_population_table_entry entry, extra_info extra, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_master_population_table</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a3c2c10dcc54c9ec95a730e4c1324a2c5</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>matches</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a84c16f8e8fdf9909791cbca87e983dde</anchor>
      <arglist>(uint32_t mp_i, uint32_t key)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_bitfields</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab9711943341e2f63e48945e4dfee5099</anchor>
      <arglist>(uint32_t mp_i, uint32_t start, uint32_t end, filter_info_t *filters)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_load_bitfields</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a4e78f94389fe12981acf2cea7e8bfe91</anchor>
      <arglist>(filter_region_t *filter_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>population_table_position_in_the_master_pop_array</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ab4759e505b101d5eb919685e2bfb55b0</anchor>
      <arglist>(spike_t spike, uint32_t *position)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5f92af4dd47e65504cbbbcb265083196</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, address_t direct_rows_address, uint32_t *row_max_n_words)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_first_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a511a4004e5621e6ec83228d4e4f94672</anchor>
      <arglist>(spike_t spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a06008941811a064b8c67dcf3a5846cde</anchor>
      <arglist>(spike_t *spike, synaptic_row_t *row_address, size_t *n_bytes_to_transfer)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>profile_tags.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>neuron_2profile__tags_8h.html</filename>
    <member kind="enumeration">
      <type></type>
      <name>profiler_tags_e</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_TIMER</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973a54cf15346177f758a5cf2bddf4584f47</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_DMA_READ</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973a23b8508f6c83d4ea5af04cef9377aebb</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_INCOMING_SPIKE</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973a06f29c1c8c010cad288570a2e846bef9</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_PROCESS_FIXED_SYNAPSES</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973a6325244b78e2b4c5f39ec14a58b9679d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_PROCESS_PLASTIC_SYNAPSES</name>
      <anchorfile>neuron_2profile__tags_8h.html</anchorfile>
      <anchor>a0d952ae768d975f73145cdb93a775973a070e57e10719c6c91dfe162487a31018</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>profile_tags.h</name>
    <path>/github/workspace/neural_modelling/src/spike_source/poisson/</path>
    <filename>spike__source_2poisson_2profile__tags_8h.html</filename>
    <member kind="enumeration">
      <type></type>
      <name>ssp_profiler_tags</name>
      <anchorfile>spike__source_2poisson_2profile__tags_8h.html</anchorfile>
      <anchor>abdc12e2df9e44bac3198456b4bdb6876</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>regions.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>regions_8h.html</filename>
    <member kind="enumeration">
      <type></type>
      <name>regions_e</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYSTEM_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6ad102acc20b0123ad06640d8c591c304f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NEURON_PARAMS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a0763e3d54f2b5ccc90f6ba223d6b68e8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYNAPSE_PARAMS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a3e4b437e3952b8683d2dde3f61a15d80</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>POPULATION_TABLE_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6aa5d73e2f95ea7659b63a96ada14f5389</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYNAPTIC_MATRIX_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6ad5778663b1d738822f9b1b5ce9dd9061</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYNAPSE_DYNAMICS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6ab672882ccd8470f490be492ed18d717b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STRUCTURAL_DYNAMICS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6acd7db540d3cd331b92037b99a0447167</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NEURON_RECORDING_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6ad275180dd412ee1f4d842871435e2440</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROVENANCE_DATA_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a9dcdca344c3940f5dabd669af51fede2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a161a63f4ef09daf69f48a49cc4a8ef5b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CONNECTOR_BUILDER_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6adb65127156b69789622d7edc85785aa9</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DIRECT_MATRIX_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a84d4ee5aba19d8207b0707272b24d31f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BIT_FIELD_FILTER_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a34f5ecbcfa6c6469d2e5d1fbbae9a55b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BIT_FIELD_BUILDER</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a9fe4b33a648c41ceae6630767bb6dd2d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BIT_FIELD_KEY_MAP</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6ad5b5a1863e094414c5fd530f7b0c42ff</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>spike_processing.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>spike__processing_8c.html</filename>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" imported="no">spike_processing.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="yes" imported="no">population_table/population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" imported="no">synapse_row.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="yes" imported="no">synapses.h</includes>
    <includes id="direct__synapses_8h" name="direct_synapses.h" local="yes" imported="no">direct_synapses.h</includes>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" imported="no">structural_plasticity/synaptogenesis_dynamics.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" imported="no">common/in_spikes.h</includes>
    <class kind="struct">dma_buffer</class>
    <member kind="define">
      <type>#define</type>
      <name>N_DMA_BUFFERS</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a0ccc8c4e5ad5471950259354965adce9</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>spike_processing_dma_tags</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>acb741a5c34907c726be786a8567abea1</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA_TAG_READ_SYNAPTIC_ROW</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>acb741a5c34907c726be786a8567abea1a1faaac0cb12a55afc649f1fd27b00f7f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA_TAG_WRITE_PLASTIC_REGION</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>acb741a5c34907c726be786a8567abea1a567fb7e55abf2d002cd50d1a25435c7f</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>do_dma_read</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ab6d3068e1fb4b07be8e94d52ded9afa6</anchor>
      <arglist>(synaptic_row_t row, size_t n_bytes_to_transfer, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>is_something_to_do</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>aad055cfcbe798048f28f1dfbce6d5296</anchor>
      <arglist>(synaptic_row_t *row, size_t *n_bytes_to_transfer, spike_t *spike, uint32_t *n_rewire, uint32_t *n_process_spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_synaptic_dma_read</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ac734bb4c991f89df03bcbe00e1f87a9f</anchor>
      <arglist>(dma_buffer *current_buffer, uint32_t *n_rewires, uint32_t *n_synapse_processes)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_synaptic_dma_write</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ad601aa61722b8a9aee3e2a7217b624d8</anchor>
      <arglist>(uint32_t dma_buffer_index, bool plastic_only)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>multicast_packet_received_callback</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a1b6621acb7633134372e8daa1010b072</anchor>
      <arglist>(uint key, uint payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>dma_complete_callback</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a318b48bbfe01e9d1142dcdfed6763d76</anchor>
      <arglist>(uint unused, uint tag)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>user_event_callback</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a1a403a9ad2200bc3bd7650e18d78fc26</anchor>
      <arglist>(uint unused0, uint unused1)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_clear_input_buffer</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>aa0ddebf0b174a40cd3406916d98f6352</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_initialise</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a27e88c158f59d59a461a579cde8f2d1f</anchor>
      <arglist>(size_t row_max_n_words, uint mc_packet_callback_priority, uint user_event_priority, uint incoming_spike_buffer_size, bool clear_input_buffers_of_late_packets_init, uint32_t packets_per_timestep_region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_buffer_overflows</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a31a23129c986ef03985d6c245cffb7ce</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_dma_complete_count</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ab28afe0154629d9ab4edf637ea0c2d7c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_spike_processing_count</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a7bb0724cd581cb5a97d52fe55957fcc7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_successful_rewires</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>abe273f1e2f87e852b3a8fc94b7029c60</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_n_packets_dropped_from_lateness</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a6d16db10b568334607d2ff3ac4d0f9eb</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_max_filled_input_buffer_size</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a666a463b005baf510746d159f90318e9</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_do_rewiring</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a392325c1b5bc32c222df0a35d3dcfad3</anchor>
      <arglist>(int number_of_rewires)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static volatile bool</type>
      <name>dma_busy</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a6d745b360c9ad1e3de0fe2ea134209f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static dma_buffer</type>
      <name>dma_buffers</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a6952d0c3ce89e17b53834243600e6745</anchor>
      <arglist>[N_DMA_BUFFERS]</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>next_buffer_to_fill</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a44ad7661afc7fed0e0bc90a36caae5db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>buffer_being_read</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a4f91d051c76c3a6e81e61a7707c277b4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static volatile uint32_t</type>
      <name>rewires_to_do</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a58209497c5fe5ba1a7034e03e6622d6d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>dma_n_rewires</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>af760c32944840948570708761ca97038</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>dma_n_spikes</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a2b782d1e539bf132657dd7c00abd91f5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>dma_complete_count</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ae5dfef7b91f7f0999e4c50dbda402c17</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>spike_processing_count</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a1c63cfe14fca20ae057b01cf442f7abc</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_successful_rewires</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a3a9f1e7d67f318a7a966f01ff80b49dd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>count_input_buffer_packets_late</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>aec7439b9895311b77cf2ee71500b4206</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>biggest_fill_size_of_input_buffer</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a4f66959943819506f9e571db16a3b0f5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>clear_input_buffers_of_late_packets</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a6553b0c9813c830009e32639e34855a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static struct @7</type>
      <name>p_per_ts_struct</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a72e1a0b25adf0ccbc7bc9d9f8ac69570</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>p_per_ts_region</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a940ad8bd79b6fbdb1fbce1341f2edf92</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>spike_processing.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>spike__processing_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" imported="no">common/in_spikes.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_initialise</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a9bca959f2f789a64fc217e2751533e96</anchor>
      <arglist>(size_t row_max_n_bytes, uint mc_packet_callback_priority, uint user_event_priority, uint incoming_spike_buffer_size, bool clear_input_buffers_of_late_packets_init, uint32_t packets_per_timestep_region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_buffer_overflows</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a31a23129c986ef03985d6c245cffb7ce</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_dma_complete_count</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>ab28afe0154629d9ab4edf637ea0c2d7c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_spike_processing_count</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a7bb0724cd581cb5a97d52fe55957fcc7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_successful_rewires</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>abe273f1e2f87e852b3a8fc94b7029c60</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_do_rewiring</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a392325c1b5bc32c222df0a35d3dcfad3</anchor>
      <arglist>(int number_of_rewires)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_n_packets_dropped_from_lateness</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a6d16db10b568334607d2ff3ac4d0f9eb</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_clear_input_buffer</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>aa0ddebf0b174a40cd3406916d98f6352</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>spike_processing_get_max_filled_input_buffer_size</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a666a463b005baf510746d159f90318e9</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>elimination.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination_8h.html</filename>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" imported="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="function">
      <type>elimination_params_t *</type>
      <name>synaptogenesis_elimination_init</name>
      <anchorfile>elimination_8h.html</anchorfile>
      <anchor>a88ffd61a2f1366e6003601838d25735e</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>synaptogenesis_elimination_rule</name>
      <anchorfile>elimination_8h.html</anchorfile>
      <anchor>afaf1f1ab83954b1d57383f2ed0161991</anchor>
      <arglist>(current_state_t *current_state, const elimination_params_t *params, uint32_t time, synaptic_row_t row)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>elimination_random_by_weight_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination__random__by__weight__impl_8c.html</filename>
    <includes id="elimination__random__by__weight__impl_8h" name="elimination_random_by_weight_impl.h" local="yes" imported="no">elimination_random_by_weight_impl.h</includes>
    <member kind="function">
      <type>elimination_params_t *</type>
      <name>synaptogenesis_elimination_init</name>
      <anchorfile>elimination__random__by__weight__impl_8c.html</anchorfile>
      <anchor>a88ffd61a2f1366e6003601838d25735e</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>elimination_random_by_weight_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination__random__by__weight__impl_8h.html</filename>
    <includes id="elimination_8h" name="elimination.h" local="yes" imported="no">elimination.h</includes>
    <class kind="struct">elimination_params</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>synaptogenesis_elimination_rule</name>
      <anchorfile>elimination__random__by__weight__impl_8h.html</anchorfile>
      <anchor>aa3392daccad8ed0eafbe912bd88066b2</anchor>
      <arglist>(current_state_t *restrict current_state, const elimination_params_t *params, uint32_t time, synaptic_row_t restrict row)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>formation.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation_8h.html</filename>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" imported="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="function">
      <type>formation_params_t *</type>
      <name>synaptogenesis_formation_init</name>
      <anchorfile>formation_8h.html</anchorfile>
      <anchor>aa02cd16c8c1854d2d163fe35f85fce6d</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>synaptogenesis_formation_rule</name>
      <anchorfile>formation_8h.html</anchorfile>
      <anchor>a4652df6d90ca06028cef7743765fe313</anchor>
      <arglist>(current_state_t *current_state, const formation_params_t *params, uint32_t time, synaptic_row_t row)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>formation_distance_dependent_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation__distance__dependent__impl_8c.html</filename>
    <includes id="formation__distance__dependent__impl_8h" name="formation_distance_dependent_impl.h" local="yes" imported="no">formation_distance_dependent_impl.h</includes>
    <member kind="function">
      <type>formation_params_t *</type>
      <name>synaptogenesis_formation_init</name>
      <anchorfile>formation__distance__dependent__impl_8c.html</anchorfile>
      <anchor>aa02cd16c8c1854d2d163fe35f85fce6d</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>formation_distance_dependent_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation__distance__dependent__impl_8h.html</filename>
    <includes id="formation_8h" name="formation.h" local="yes" imported="no">formation.h</includes>
    <class kind="struct">formation_params</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_SHORT</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a3742efaf988af88c727a30ca9d8d993f</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int</type>
      <name>my_abs</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>ad50b05a6a57eb92bc38867ef0c89dd8a</anchor>
      <arglist>(int a)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>synaptogenesis_formation_rule</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a4652df6d90ca06028cef7743765fe313</anchor>
      <arglist>(current_state_t *current_state, const formation_params_t *params, uint32_t time, synaptic_row_t row)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>last_neuron_selection_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>last__neuron__selection__impl_8c.html</filename>
    <includes id="last__neuron__selection__impl_8h" name="last_neuron_selection_impl.h" local="yes" imported="no">last_neuron_selection_impl.h</includes>
    <member kind="function">
      <type>void</type>
      <name>partner_init</name>
      <anchorfile>last__neuron__selection__impl_8c.html</anchorfile>
      <anchor>aa0c616a50e494c67ae9c1066a5d8df23</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
    <member kind="variable">
      <type>spike_t *</type>
      <name>last_spikes_buffer</name>
      <anchorfile>last__neuron__selection__impl_8c.html</anchorfile>
      <anchor>a0c6ea3029fe958000e3697db978f4db7</anchor>
      <arglist>[2]</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes</name>
      <anchorfile>last__neuron__selection__impl_8c.html</anchorfile>
      <anchor>a3517ef59d8e5a261be447e890013b160</anchor>
      <arglist>[2]</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>last_spikes_buffer_size</name>
      <anchorfile>last__neuron__selection__impl_8c.html</anchorfile>
      <anchor>a1426be5faa3cda06aba963af47402da6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>last_time</name>
      <anchorfile>last__neuron__selection__impl_8c.html</anchorfile>
      <anchor>adf31bd4dca7310ba032781bf74fee32c</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>last_neuron_selection_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>last__neuron__selection__impl_8h.html</filename>
    <includes id="partner_8h" name="partner.h" local="yes" imported="no">partner.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="no" imported="no">neuron/spike_processing.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>partner_spike_received</name>
      <anchorfile>last__neuron__selection__impl_8h.html</anchorfile>
      <anchor>ac996afd22014e8bbc3106e0f84cddc7e</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>potential_presynaptic_partner</name>
      <anchorfile>last__neuron__selection__impl_8h.html</anchorfile>
      <anchor>acf4961684ee5730d0017dc34c1a8211d</anchor>
      <arglist>(uint32_t time, uint32_t *restrict population_id, uint32_t *restrict sub_population_id, uint32_t *restrict neuron_id, spike_t *restrict spike, uint32_t *restrict m_pop_index)</arglist>
    </member>
    <member kind="variable">
      <type>spike_t *</type>
      <name>last_spikes_buffer</name>
      <anchorfile>last__neuron__selection__impl_8h.html</anchorfile>
      <anchor>a0c6ea3029fe958000e3697db978f4db7</anchor>
      <arglist>[2]</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes</name>
      <anchorfile>last__neuron__selection__impl_8h.html</anchorfile>
      <anchor>a3517ef59d8e5a261be447e890013b160</anchor>
      <arglist>[2]</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>partner.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>partner_8h.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="no" imported="no">neuron/synapses.h</includes>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" imported="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="define">
      <type>#define</type>
      <name>INVALID_SELECTION</name>
      <anchorfile>partner_8h.html</anchorfile>
      <anchor>a2a7bcb70c4ad5d6f163e74c8fa035f91</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>partner_init</name>
      <anchorfile>partner_8h.html</anchorfile>
      <anchor>aa0c616a50e494c67ae9c1066a5d8df23</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>partner_spike_received</name>
      <anchorfile>partner_8h.html</anchorfile>
      <anchor>ac996afd22014e8bbc3106e0f84cddc7e</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>potential_presynaptic_partner</name>
      <anchorfile>partner_8h.html</anchorfile>
      <anchor>acf4961684ee5730d0017dc34c1a8211d</anchor>
      <arglist>(uint32_t time, uint32_t *restrict population_id, uint32_t *restrict sub_population_id, uint32_t *restrict neuron_id, spike_t *restrict spike, uint32_t *restrict m_pop_index)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>random_selection_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>random__selection__impl_8c.html</filename>
    <includes id="random__selection__impl_8h" name="random_selection_impl.h" local="yes" imported="no">random_selection_impl.h</includes>
    <member kind="function">
      <type>void</type>
      <name>partner_init</name>
      <anchorfile>random__selection__impl_8c.html</anchorfile>
      <anchor>aa0c616a50e494c67ae9c1066a5d8df23</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>random_selection_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>random__selection__impl_8h.html</filename>
    <includes id="partner_8h" name="partner.h" local="yes" imported="no">partner.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="no" imported="no">neuron/spike_processing.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>partner_spike_received</name>
      <anchorfile>random__selection__impl_8h.html</anchorfile>
      <anchor>ac996afd22014e8bbc3106e0f84cddc7e</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>potential_presynaptic_partner</name>
      <anchorfile>random__selection__impl_8h.html</anchorfile>
      <anchor>acf4961684ee5730d0017dc34c1a8211d</anchor>
      <arglist>(uint32_t time, uint32_t *restrict population_id, uint32_t *restrict sub_population_id, uint32_t *restrict neuron_id, spike_t *restrict spike, uint32_t *restrict m_pop_index)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>sp_structs.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/</path>
    <filename>sp__structs_8h.html</filename>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="no" imported="no">neuron/plasticity/synapse_dynamics.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <class kind="struct">post_to_pre_entry</class>
    <class kind="struct">key_atom_info_t</class>
    <class kind="struct">pre_info_t</class>
    <class kind="struct">pre_pop_info_table_t</class>
    <class kind="struct">rewiring_data_t</class>
    <class kind="struct">current_state_t</class>
    <member kind="define">
      <type>#define</type>
      <name>IS_CONNECTION_LAT</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a8ee9a5f54a9347b84ef109d9f9fd1fa5</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>rand_int</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>abfe9bbac4f366e370a68a174d26c0261</anchor>
      <arglist>(uint32_t max, mars_kiss64_seed_t seed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>sp_structs_find_by_spike</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>aca9cfbe9add5978e97d5fe58039b2d3b</anchor>
      <arglist>(const pre_pop_info_table_t *pre_pop_info_table, spike_t spike, uint32_t *restrict neuron_id, uint32_t *restrict population_id, uint32_t *restrict sub_population_id, uint32_t *restrict m_pop_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>sp_structs_get_sub_pop_info</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>ad2579659b57fc47437537823688e2315</anchor>
      <arglist>(const pre_pop_info_table_t *pre_pop_info_table, uint32_t population_id, uint32_t pop_neuron_id, uint32_t *restrict sub_population_id, uint32_t *restrict sub_pop_neuron_id, uint32_t *restrict spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>sp_structs_remove_synapse</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a556a46199d62d23cdff354c53b2c7906</anchor>
      <arglist>(current_state_t *restrict current_state, synaptic_row_t restrict row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>sp_structs_add_synapse</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a430fd8b92b5f0b7a6b523de8b692cc9d</anchor>
      <arglist>(current_state_t *restrict current_state, synaptic_row_t restrict row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint8_t *</type>
      <name>sp_structs_read_in_common</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>af0f53340995f427043f318c118d3d974</anchor>
      <arglist>(address_t sdram_sp_address, rewiring_data_t *rewiring_data, pre_pop_info_table_t *pre_info, post_to_pre_entry **post_to_pre_table)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>topographic_map_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/synaptogenesis/</path>
    <filename>topographic__map__impl_8c.html</filename>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="no" imported="no">neuron/structural_plasticity/synaptogenesis_dynamics.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="no" imported="no">neuron/population_table/population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="no" imported="no">neuron/synapses.h</includes>
    <includes id="maths-util_8h" name="maths-util.h" local="no" imported="no">common/maths-util.h</includes>
    <includes id="partner_8h" name="partner.h" local="yes" imported="no">partner_selection/partner.h</includes>
    <includes id="elimination_8h" name="elimination.h" local="yes" imported="no">elimination/elimination.h</includes>
    <includes id="formation_8h" name="formation.h" local="yes" imported="no">formation/formation.h</includes>
    <member kind="function">
      <type>void</type>
      <name>print_post_to_pre_entry</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aa905464bd5cc1eb8fa5b1b16b0d9b263</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_initialise</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>adba45d439e3c65751b2508e6ae744e15</anchor>
      <arglist>(address_t sdram_sp_address)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a5cdd3772a85bf8d042932b9ec4e57125</anchor>
      <arglist>(uint32_t time, spike_t *spike, synaptic_row_t *synaptic_row, uint32_t *n_bytes)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>row_restructure</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aa1038fc3912a348ccc5b2f3331181a98</anchor>
      <arglist>(uint32_t time, synaptic_row_t restrict row, current_state_t *restrict current_state)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_row_restructure</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>ac97a88bbadb38fa4d4a67aa86aa615c8</anchor>
      <arglist>(uint32_t time, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>int32_t</type>
      <name>synaptogenesis_rewiring_period</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>afa57eee149b8ef2c30e2239c22f0957e</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_is_fast</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a0d2bd7f05bdc3f4c8ce1ccafc16feb4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="variable">
      <type>rewiring_data_t</type>
      <name>rewiring_data</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a14052fb746b24752fc5a96accf39d8b8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static post_to_pre_entry *</type>
      <name>post_to_pre_table</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>ab4adc13b137ccdbaff9d8883400182eb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>pre_pop_info_table_t</type>
      <name>pre_info</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a25e63ee99aecac3677f299c1cccec889</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static formation_params_t **</type>
      <name>formation_params</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a9eaecb5e1c8b325fcd3d6f500f15875f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static elimination_params_t **</type>
      <name>elimination_params</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aa964e9c3a6560d7521d1c40f9825fb8a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static circular_buffer</type>
      <name>current_state_queue</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a617d5ccf1e27648321a85cfc2498eedf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static circular_buffer</type>
      <name>free_states</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>abe30d6dd9444f9a17ed9128f6682fa03</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synaptogenesis_dynamics.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/</path>
    <filename>synaptogenesis__dynamics_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_initialise</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>adba45d439e3c65751b2508e6ae744e15</anchor>
      <arglist>(address_t sdram_sp_address)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a5cdd3772a85bf8d042932b9ec4e57125</anchor>
      <arglist>(uint32_t time, spike_t *spike, synaptic_row_t *synaptic_row, uint32_t *n_bytes)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_row_restructure</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>ac97a88bbadb38fa4d4a67aa86aa615c8</anchor>
      <arglist>(uint32_t time, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>int32_t</type>
      <name>synaptogenesis_rewiring_period</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>afa57eee149b8ef2c30e2239c22f0957e</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_is_fast</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a0d2bd7f05bdc3f4c8ce1ccafc16feb4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>print_post_to_pre_entry</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>aa905464bd5cc1eb8fa5b1b16b0d9b263</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synaptogenesis_dynamics_static_impl.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/structural_plasticity/</path>
    <filename>synaptogenesis__dynamics__static__impl_8c.html</filename>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" imported="no">synaptogenesis_dynamics.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_initialise</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>adba45d439e3c65751b2508e6ae744e15</anchor>
      <arglist>(address_t sdram_sp_address)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a5cdd3772a85bf8d042932b9ec4e57125</anchor>
      <arglist>(uint32_t time, spike_t *spike, synaptic_row_t *synaptic_row, uint32_t *n_bytes)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_row_restructure</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>ac97a88bbadb38fa4d4a67aa86aa615c8</anchor>
      <arglist>(uint32_t time, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>int32_t</type>
      <name>synaptogenesis_rewiring_period</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>afa57eee149b8ef2c30e2239c22f0957e</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_is_fast</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a0d2bd7f05bdc3f4c8ce1ccafc16feb4a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>print_post_to_pre_entry</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>aa905464bd5cc1eb8fa5b1b16b0d9b263</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_row.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>synapse__row_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <class kind="struct">synapse_row_plastic_part_t</class>
    <class kind="struct">synapse_row_fixed_part_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_WEIGHT_BITS</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a6e5ee3925245f54cf5f6c4312338c25c</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_DELAY_BITS</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a28b2156b2573ab59559866710ed97628</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_DELAY_MASK</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a9932d3e682ca42eb572c28a676e4e4b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>N_SYNAPSE_ROW_HEADER_WORDS</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ad7cd5d97013df7e40e5a1f2c7d73ee57</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>uint16_t</type>
      <name>control_t</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>aeae1e8aa0c0095434ba488866ef21aa2</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static size_t</type>
      <name>synapse_row_plastic_size</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ab9de8a1b79ad078f892038e4051781d0</anchor>
      <arglist>(const synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static synapse_row_plastic_data_t *</type>
      <name>synapse_row_plastic_region</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ab4d844ff18533819cb6793bbe6fbacd9</anchor>
      <arglist>(synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static synapse_row_fixed_part_t *</type>
      <name>synapse_row_fixed_region</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a3c97c04cad6ef6f8546f9a12ed296661</anchor>
      <arglist>(synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static size_t</type>
      <name>synapse_row_num_fixed_synapses</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a8c35d5f7f5f1cb6929f948549e91b47e</anchor>
      <arglist>(const synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static size_t</type>
      <name>synapse_row_num_plastic_controls</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a1a67df8c1a740101c0a92eec74c26760</anchor>
      <arglist>(const synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static control_t *</type>
      <name>synapse_row_plastic_controls</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>aa4cf1bbc1757f4668733006a24cd87b9</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t *</type>
      <name>synapse_row_fixed_weight_controls</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a3155272454c2d645bad4291002b5a65e</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_sparse_index</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a9bbd252568935c8020f478dcdaff97b5</anchor>
      <arglist>(uint32_t x, uint32_t synapse_index_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_sparse_type</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a8ac7fef74256d744079d84a638d2d5c7</anchor>
      <arglist>(uint32_t x, uint32_t synapse_index_bits, uint32_t synapse_type_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_sparse_type_index</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ab47a817128850c7fea9d755816040392</anchor>
      <arglist>(uint32_t x, uint32_t synapse_type_index_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_sparse_delay</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a8ac4945585bcd95397c6ab7f57e413f7</anchor>
      <arglist>(uint32_t x, uint32_t synapse_type_index_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_row_sparse_weight</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>af7eb0b5869f5256cf8a1343860d8aa21</anchor>
      <arglist>(uint32_t x)</arglist>
    </member>
    <docanchor file="synapse__row_8h.html" title="Synapse Row Representation">row</docanchor>
    <docanchor file="synapse__row_8h.html" title="Data Structure">matrix</docanchor>
    <docanchor file="synapse__row_8h.html" title="Fixed and Fixed-Plastic Regions">fixed</docanchor>
  </compound>
  <compound kind="file">
    <name>synapse_types.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" imported="no">neuron/synapse_row.h</includes>
    <member kind="typedef">
      <type>synapse_param_t *</type>
      <name>synapse_param_pointer_t</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a45cfd57493ca66ddc880bd013f1022fe</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>aebfa05875ff9afaae47150029297e087</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_alpha_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types__alpha__impl_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" imported="no">neuron/decay.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" imported="no">synapse_types.h</includes>
    <class kind="struct">alpha_params_t</class>
    <class kind="struct">synapse_param_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_BITS</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a6a9484756434bfd11111a5187ac8f4bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_COUNT</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a5be51be8977cd8a1209495229df7c491</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>synapse_alpha_input_buffer_regions</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a3fc30879d6f7f95782bfeeccbca6bb20</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a3fc30879d6f7f95782bfeeccbca6bb20a5e0e3eedcc62dc4db0c7e2af83703129</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INHIBITORY</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a3fc30879d6f7f95782bfeeccbca6bb20a175c96e554c8359207394ef1e677b70d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>alpha_shaping</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a595d73638412233a14d1ac8462421c85</anchor>
      <arglist>(alpha_params_t *a_params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_alpha</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a6f1daf43aec061c87d2cfe8cf23ca667</anchor>
      <arglist>(alpha_params_t *a_params, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>aebfa05875ff9afaae47150029297e087</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_delta_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types__delta__impl_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" imported="no">synapse_types.h</includes>
    <class kind="struct">delta_params_t</class>
    <class kind="struct">synapse_param_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_BITS</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a6a9484756434bfd11111a5187ac8f4bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_COUNT</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a5be51be8977cd8a1209495229df7c491</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>synapse_delta_input_buffer_regions</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>afcd85a8de2d9bb81e9a220ddf1427841</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>afcd85a8de2d9bb81e9a220ddf1427841a5e0e3eedcc62dc4db0c7e2af83703129</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INHIBITORY</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>afcd85a8de2d9bb81e9a220ddf1427841a175c96e554c8359207394ef1e677b70d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>delta_shaping</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>aefa7a5c5b0733fa2e07811fc7f4bf646</anchor>
      <arglist>(delta_params_t *delta_param)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_delta</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a4ad32bf38141af059e3de4e3d29fcb52</anchor>
      <arglist>(delta_params_t *delta_param, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>aebfa05875ff9afaae47150029297e087</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_dual_excitatory_exponential_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types__dual__excitatory__exponential__impl_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" imported="no">neuron/decay.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" imported="no">synapse_types.h</includes>
    <class kind="struct">exp_params_t</class>
    <class kind="struct">synapse_param_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_BITS</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a6a9484756434bfd11111a5187ac8f4bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_COUNT</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a5be51be8977cd8a1209495229df7c491</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>synapse_dual_input_buffer_regions</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a5e42ec2b0d3c67e38a79be2f1d457b51</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY_ONE</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a5e42ec2b0d3c67e38a79be2f1d457b51ae7536bbfd551e2b571749964e82cfd5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY_TWO</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a5e42ec2b0d3c67e38a79be2f1d457b51ac7f31813b08e992fff7171fb726aae2f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INHIBITORY</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a5e42ec2b0d3c67e38a79be2f1d457b51a175c96e554c8359207394ef1e677b70d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>exp_shaping</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a95a70b829aa4c8502819828a2f7e28f0</anchor>
      <arglist>(exp_params_t *exp_param)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_exp</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a6f6553c51eb2199989cc1e7ca9f16b71</anchor>
      <arglist>(exp_params_t *exp_param, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>aebfa05875ff9afaae47150029297e087</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_exponential_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types__exponential__impl_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" imported="no">neuron/decay.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" imported="no">synapse_types.h</includes>
    <class kind="struct">exp_params_t</class>
    <class kind="struct">synapse_param_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_BITS</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a6a9484756434bfd11111a5187ac8f4bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_COUNT</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a5be51be8977cd8a1209495229df7c491</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>exponential_synapse_input_buffer_regions</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>aa8f436b9633d82c53bcbeea73f3eb4ab</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>aa8f436b9633d82c53bcbeea73f3eb4aba5e0e3eedcc62dc4db0c7e2af83703129</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INHIBITORY</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>aa8f436b9633d82c53bcbeea73f3eb4aba175c96e554c8359207394ef1e677b70d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>exp_shaping</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a95a70b829aa4c8502819828a2f7e28f0</anchor>
      <arglist>(exp_params_t *exp_param)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_exp</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a6f6553c51eb2199989cc1e7ca9f16b71</anchor>
      <arglist>(exp_params_t *exp_param, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>aebfa05875ff9afaae47150029297e087</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_semd_impl.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/synapse_types/</path>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" imported="no">neuron/decay.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" imported="no">synapse_types.h</includes>
    <class kind="struct">exp_params_t</class>
    <class kind="struct">synapse_param_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_BITS</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a6a9484756434bfd11111a5187ac8f4bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_TYPE_COUNT</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a5be51be8977cd8a1209495229df7c491</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_EXCITATORY_RECEPTORS</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ad780fbb2c43b8bbf0f73ff0561061174</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NUM_INHIBITORY_RECEPTORS</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a6dd746ed60f4dc54e7e604f239843aa6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>synapse_semd_input_buffer_regions</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac5bb58bf4fa0e9ea571c2a09f810b511</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY_ONE</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac5bb58bf4fa0e9ea571c2a09f810b511ae7536bbfd551e2b571749964e82cfd5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXCITATORY_TWO</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac5bb58bf4fa0e9ea571c2a09f810b511ac7f31813b08e992fff7171fb726aae2f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INHIBITORY</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac5bb58bf4fa0e9ea571c2a09f810b511a175c96e554c8359207394ef1e677b70d</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>exp_shaping</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a95a70b829aa4c8502819828a2f7e28f0</anchor>
      <arglist>(exp_params_t *exp_param)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a9252e28ec9676ec472c3128ff88c368d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_exp</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a49fd1a10ec209bdebb87d116fcd8d1a9</anchor>
      <arglist>(exp_params_t *parameter, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>acf288f16ad00e587ffe9057de91c5b4e</anchor>
      <arglist>(index_t synapse_type_index, synapse_param_t *parameter, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a445fbc87ae924aa89de5d72e6841cad6</anchor>
      <arglist>(input_t *excitatory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ae4d30d854f0664fe4cef10f4ecc00831</anchor>
      <arglist>(input_t *inhibitory_response, synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a33e2109c0192ac4353dd6b2de44e1bed</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a4d26d3dff1703c07eca4dbf846a0946d</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a8c173175ef5d71b07f3bc7d511cc11c7</anchor>
      <arglist>(synapse_param_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapses.c</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>synapses_8c.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="yes" imported="no">synapses.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" imported="no">spike_processing.h</includes>
    <includes id="neuron_8h" name="neuron.h" local="yes" imported="no">neuron.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" imported="no">plasticity/synapse_dynamics.h</includes>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>get_type_char</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a5af3d86ffc14ed6815aeeec7dbe9412a</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_synaptic_row</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a6ce61ebd9de50e3e1d657fd651038879</anchor>
      <arglist>(synaptic_row_t synaptic_row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_ring_buffers</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>abc3c16c46a33ff2d2b041797a591963f</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_inputs</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a445b2a82a1dd66ace9f61be6d2fc0bdb</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>process_fixed_synapses</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a1d201e7f33249ba424c34d09b79e2be2</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed_region, uint32_t time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_synapse_parameters</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a74c97ada7fedd1b5e90ed09797072c29</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_initialise</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a5b2663443fdda5a87da4b66e49a5d0e4</anchor>
      <arglist>(address_t synapse_params_address, uint32_t n_neurons_value, uint32_t n_synapse_types_value, uint32_t **ring_buffer_to_input_buffer_left_shifts, bool *clear_input_buffers_of_late_packets_init)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_do_timestep_update</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ad88a7e6b3773f1e0f334b7410f182987</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_process_synaptic_row</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>aa1ceab23dea834d6189f496b5133d983</anchor>
      <arglist>(uint32_t time, synaptic_row_t row, bool *write_back)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapses_get_pre_synaptic_events</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>aa95d63df3a6fbedaaf3a0d36f824df35</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_flush_ring_buffers</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a71374045de8f83cde4a8a44bbd421ffd</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_shut_down</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ac237268af6684b631aef510cc52fa607</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>num_fixed_pre_synaptic_events</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ad0a74ab015d7bf121e773b5ccd167ced</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_neurons</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a7368643a28282d8b3429f0fb145aa5db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_synapse_types</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>adedb27b3ece4d4dece0aee776a136427</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static weight_t *</type>
      <name>ring_buffers</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a9d013c2e9d5eddd8472bd57e9b21ff99</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>ring_buffer_size</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a9c43ae0578a77accabf5614e5788020b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t *</type>
      <name>ring_buffer_to_input_left_shifts</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ade696d20461dc712b7daafcbcad6ba4b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_index_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ac3299a10c6a78f6e4f37246ab79a0736</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_index_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a84db6c41c7cf03558016d477d8df4d37</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>af20079aa1e3c31a3efd344176025ce0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_type_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>af786c2a0c6f40c688029991d5b9711a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapses_saturation_count</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a8b7881a6d9caca38f2050656c652cf26</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapses.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/</path>
    <filename>synapses_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" imported="no">synapse_row.h</includes>
    <includes id="neuron_8h" name="neuron.h" local="yes" imported="no">neuron.h</includes>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapses_get_ring_buffer_index</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a3f256864c3f363b43d3b44c939841742</anchor>
      <arglist>(uint32_t simulation_timestep, uint32_t synapse_type_index, uint32_t neuron_index, uint32_t synapse_type_index_bits, uint32_t synapse_index_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapses_get_ring_buffer_index_combined</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a26a09bf4d0cc9d60690e8a17d5c967cd</anchor>
      <arglist>(uint32_t simulation_timestep, uint32_t combined_synapse_neuron_index, uint32_t synapse_type_index_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>synapses_convert_weight_to_input</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>ac7151e725b13e2e92e35e95997d41194</anchor>
      <arglist>(weight_t weight, uint32_t left_shift)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapses_print_weight</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>aa1ad92bb519344d001dba972cdd0be5f</anchor>
      <arglist>(weight_t weight, uint32_t left_shift)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_initialise</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>afb7de7af1598c0248a5ac78921afadef</anchor>
      <arglist>(address_t synapse_params_address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t **ring_buffer_to_input_buffer_left_shifts, bool *clear_input_buffers_of_late_packets_init)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_do_timestep_update</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>ad88a7e6b3773f1e0f334b7410f182987</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_process_synaptic_row</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>aa1ceab23dea834d6189f496b5133d983</anchor>
      <arglist>(uint32_t time, synaptic_row_t row, bool *write_back)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapses_get_pre_synaptic_events</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>aa95d63df3a6fbedaaf3a0d36f824df35</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_flush_ring_buffers</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a71374045de8f83cde4a8a44bbd421ffd</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_shut_down</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>ac237268af6684b631aef510cc52fa607</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapses_saturation_count</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a8b7881a6d9caca38f2050656c652cf26</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>threshold_type.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/threshold_types/</path>
    <filename>threshold__type_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <member kind="typedef">
      <type>threshold_type_t *</type>
      <name>threshold_type_pointer_t</name>
      <anchorfile>threshold__type_8h.html</anchorfile>
      <anchor>a52fff0cbae0aee9e6dc7ad0e209511dd</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>threshold_type_is_above_threshold</name>
      <anchorfile>threshold__type_8h.html</anchorfile>
      <anchor>a78e80ccc57135aa9f338b0e82001fb89</anchor>
      <arglist>(state_t value, threshold_type_t *threshold_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>threshold_type_maass_stochastic.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/threshold_types/</path>
    <filename>threshold__type__maass__stochastic_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" imported="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_t</class>
    <member kind="define">
      <type>#define</type>
      <name>PROB_SATURATION</name>
      <anchorfile>threshold__type__maass__stochastic_8h.html</anchorfile>
      <anchor>a83a285b76d1d37dc508e758e1f0c9726</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>threshold_type_is_above_threshold</name>
      <anchorfile>threshold__type__maass__stochastic_8h.html</anchorfile>
      <anchor>a78e80ccc57135aa9f338b0e82001fb89</anchor>
      <arglist>(state_t value, threshold_type_t *threshold_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>threshold_type_none.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/threshold_types/</path>
    <filename>threshold__type__none_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" imported="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_t</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>threshold_type_is_above_threshold</name>
      <anchorfile>threshold__type__none_8h.html</anchorfile>
      <anchor>a78e80ccc57135aa9f338b0e82001fb89</anchor>
      <arglist>(state_t value, threshold_type_t *threshold_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>threshold_type_static.h</name>
    <path>/github/workspace/neural_modelling/src/neuron/threshold_types/</path>
    <filename>threshold__type__static_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" imported="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_t</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>threshold_type_is_above_threshold</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a78e80ccc57135aa9f338b0e82001fb89</anchor>
      <arglist>(state_t value, threshold_type_t *threshold_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>robot_motor_control.c</name>
    <path>/github/workspace/neural_modelling/src/robot_motor_control/</path>
    <filename>robot__motor__control_8c.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" imported="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" imported="no">common/in_spikes.h</includes>
    <class kind="struct">motor_control_config_t</class>
    <class kind="struct">robot_motor_control_provenance</class>
    <member kind="define">
      <type>#define</type>
      <name>N_COUNTERS</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>af0514f49bd1003dd50d375abf557b50a</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NEURON_ID_MASK</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a00cd32915a371b81b181def080b6d66c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>direction_t</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_FORWARD</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6ba8b2dd5740ac43f280ecb85ae466d1028</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_BACK</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6ba900cc6499a525a734cb344393423500f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_RIGHT</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6ba910d963167fc6be93e9de05d58ab9fc1</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_LEFT</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6bacd6489b49063ff655e722f70e18b1ab3</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_CLOCKWISE</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6ba99000b0392476f351f829e90f2103de3</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MOTION_C_CLOCKWISE</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae9ae980041e438eed7a3af43ce4e9f6ba90db4a094b402628361e3614f518c7a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>robot_motor_control_regions_e</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a7f61ffa202f9ba34d1917f6f83d8bf9d</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYSTEM_REGION</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a7f61ffa202f9ba34d1917f6f83d8bf9dad102acc20b0123ad06640d8c591c304f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PARAMS_REGION</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a7f61ffa202f9ba34d1917f6f83d8bf9da91faf3838b3b1ca64895b4f7bc331410</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROVENANCE_DATA_REGION</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a7f61ffa202f9ba34d1917f6f83d8bf9da9dcdca344c3940f5dabd669af51fede2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>robot_motor_control_callback_priorities</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ad8ff0294897e11d77bb67c6f1e9a3386</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MC</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ad8ff0294897e11d77bb67c6f1e9a3386a8e15ed3aa6ccc02e22b283c8bd0b4096</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SDP</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ad8ff0294897e11d77bb67c6f1e9a3386ad645defae8408de2415f3dc417f69773</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ad8ff0294897e11d77bb67c6f1e9a3386a6537a62f6f155792bb9a320ee2ec4d68</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TIMER</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ad8ff0294897e11d77bb67c6f1e9a3386a17ba9bae1b8d7e8d6c12d46ec58e0769</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>send_to_motor</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a9d116f770371127474391640debce621</anchor>
      <arglist>(uint32_t direction, uint32_t the_speed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>do_motion</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a96363d8d245d659d10d5512cb46aa0e3</anchor>
      <arglist>(direction_t direction_index, direction_t opposite_index, const char *direction, const char *opposite)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>do_update</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a559960c23f8a6e90bde4d3e5b8dc7811</anchor>
      <arglist>(direction_t direction_index, direction_t opposite_index, const char *direction, const char *opposite)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>timer_callback</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>aa51de182df34173453b5d99dcd2ffedc</anchor>
      <arglist>(uint unused0, uint unused1)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>read_parameters</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>aa23e1c102ba93d20434d86c3fda24fce</anchor>
      <arglist>(motor_control_config_t *config_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>incoming_spike_callback</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a95885055138e174e0b8e70fcafa07388</anchor>
      <arglist>(uint key, uint payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>incoming_spike_callback_payload</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a55ebafbff10f99685495e8f745ff53ca</anchor>
      <arglist>(uint key, uint payload)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>c_main_store_provenance_data</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a1dc4d17392d4c0a6dac7ab12267da487</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialize</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a37f0b2315f3101f6ff9936c212c5bd84</anchor>
      <arglist>(uint32_t *timer_period)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int *</type>
      <name>counters</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a3b08ec26bdf4328bdc94c955dfab05b3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int *</type>
      <name>last_speed</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ada328500a397b9cc689fd84ba7f92adb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>key</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a6d4ec8e4f3148d51041635da9986c3fa</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int</type>
      <name>speed</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a218b4f7c6cc2681a99c23a3b089d68b1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>sample_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ab322aee7201d11451cb55e2f551e72cb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>update_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a86e18fc3ab6be6646e80307e68187e63</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>delay_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a293f27a9ee99a155bbebd8f77049f462</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static int</type>
      <name>delta_threshold</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a09517e37541b1afcae42a85569fd6976</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bool</type>
      <name>continue_if_not_different</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a6526db077be7f7eaa67bf3bf25800eeb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>spike_source_poisson.c</name>
    <path>/github/workspace/neural_modelling/src/spike_source/poisson/</path>
    <filename>spike__source__poisson_8c.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="no" imported="no">common/maths-util.h</includes>
    <includes id="spike__source_2poisson_2profile__tags_8h" name="profile_tags.h" local="yes" imported="no">profile_tags.h</includes>
    <class kind="struct">spike_source_t</class>
    <class kind="struct">timed_out_spikes</class>
    <class kind="struct">global_parameters</class>
    <class kind="struct">poisson_extension_provenance</class>
    <class kind="struct">source_info</class>
    <member kind="define">
      <type>#define</type>
      <name>NUMBER_OF_REGIONS_TO_RECORD</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a9460522d5774f317649cd352ea6112b0</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>BYTE_TO_WORD_CONVERTER</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a60ccdb9b7cf99da446d1b7a8a27a55a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>ISI_SCALE_FACTOR</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>af9fc996bed279eea4da4fd5166df447c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>region</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SYSTEM</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a57cc238145ec1361c72c327674c0d754</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>POISSON_PARAMS</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a727a4355ea4eac05e783bca4d11a76de</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>RATES</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a7f669c928768a61926bf55f39d53528a</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SPIKE_HISTORY_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a162ff910476c1b005ba3214e83f68b27</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROVENANCE_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a43f0d58cfc0317ea06139b20c9242d1e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PROFILER_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a161a63f4ef09daf69f48a49cc4a8ef5b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TDMA_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a3ec559988321d901a9631875c4782ba6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>callback_priorities</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>MULTICAST</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a607d700b2c0a01c54bdadde074a7cb12</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>SDP</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964ad645defae8408de2415f3dc417f69773</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>DMA</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a6537a62f6f155792bb9a320ee2ec4d68</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>TIMER</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964a17ba9bae1b8d7e8d6c12d46ec58e0769</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>store_provenance_data</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6a6f18428eca2d03be2d82834e642876</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static spike_source_t *</type>
      <name>get_source_data</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a271dd89ae6f3a25d49a7e2d4cb768a37</anchor>
      <arglist>(uint32_t id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bit_field_t</type>
      <name>out_spikes_bitfield</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>af538c1942ccd68490d03067fae37805b</anchor>
      <arglist>(uint32_t n)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>reset_spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6965b6994e494500e00730df56c449b5</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>slow_spike_source_get_time_to_spike</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa2602e67f1b5a03f8e9440743171ef81</anchor>
      <arglist>(uint32_t mean_inter_spike_interval_in_ticks)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>fast_spike_source_get_num_spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6fc68d58ed86cf64bddcb8c1a16c101d</anchor>
      <arglist>(UFRACT exp_minus_lambda)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>faster_spike_source_get_num_spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a44e2906c713931da0ee4f911361afc5f</anchor>
      <arglist>(REAL sqrt_lambda)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_spike_source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a01cb7fc152ba6cfcdef074e29129fd50</anchor>
      <arglist>(index_t s)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_spike_sources</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a67624c118e9bb7a0b4d9da6aa5afd523</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_global_parameters</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a571b747b9d964eb5af02496ce866130b</anchor>
      <arglist>(global_parameters *sdram_globals)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>read_next_rates</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a5d93135c80cbb663f602737e639626ce</anchor>
      <arglist>(uint32_t id)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_rates</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>af4847de2b9a2d080b0e03eabccb7308d</anchor>
      <arglist>(source_info *sdram_sources)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise_recording</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a25d26d2a2c3ec75e4013c7a5e42bc5a7</anchor>
      <arglist>(data_specification_metadata_t *ds_regions)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialize</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a03a8e4045b51680cc94b4359837fa796</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>resume_callback</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>afb40f588131f69f1d033283921f1a811</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>store_poisson_parameters</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ad3f5360b39be7e95723ff26506d24fbe</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>expand_spike_recording_buffer</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a09166600548501c6befb79b410cdc98a</anchor>
      <arglist>(uint32_t n_spikes)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>mark_spike</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a285c14edf54c74a6fe624e2968964a12</anchor>
      <arglist>(uint32_t neuron_id, uint32_t n_spikes)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>record_spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6383f32ff6d54333f83d681ff919d4d0</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>process_fast_source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a8c0f1543e08e9c0d5ea8ac638f65fdac</anchor>
      <arglist>(index_t s_id, spike_source_t *source, uint timer_count)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>process_slow_source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ae6b1e1c0aee533b40075573aca35b72f</anchor>
      <arglist>(index_t s_id, spike_source_t *source, uint timer_count)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>timer_callback</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab3ba3db2e11b1db9fd9d1986558eee30</anchor>
      <arglist>(uint timer_count, uint unused)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>set_spike_source_rate</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a12c72782cb450237076bc0622fc90125</anchor>
      <arglist>(uint32_t id, REAL rate)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>multicast_packet_callback</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>af5b2c04c7a9d81f1421e15ddfe40b782</anchor>
      <arglist>(uint key, uint payload)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>uint</type>
      <name>ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a7fcd6915876e066781399d7b00f1b1f0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static global_parameters</type>
      <name>ssp_params</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a3474215ce02c1bf76bceafe71ef89c7b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static source_info **</type>
      <name>source_data</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a47b4faf584a02b7d913efcb91134d196</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static spike_source_t *</type>
      <name>source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a8fc9649bde3c5a1307c82861ad881004</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>recording_flags</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a9a97f21dc7fccaac8071bcd29894bccb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>time</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static timed_out_spikes *</type>
      <name>spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa0bfbeceddbbc2213395ff3ffce6f548</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spike_buffers_allocated</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a9bd59adaf862fb5e262d0bc6fb6b0bfb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spike_buffer_words</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab75c33a373a49cc4235f559fc559b0f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>spike_buffer_size</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>afdae215608627a97110d1cd913398563</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_period</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ac0c27301e134af3ce80814a553601074</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>common_kernel.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>common__kernel_8c.html</filename>
    <includes id="common__kernel_8h" name="common_kernel.h" local="yes" imported="no">common_kernel.h</includes>
    <member kind="function">
      <type>uint16_t</type>
      <name>uidiv</name>
      <anchorfile>common__kernel_8c.html</anchorfile>
      <anchor>ac7271db2d65d3c345c76024e1becfe99</anchor>
      <arglist>(uint32_t dividend, uint16_t divider, uint16_t *remainder)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>post_in_pre_world</name>
      <anchorfile>common__kernel_8c.html</anchorfile>
      <anchor>ae380e1c9722449c4ef92aa2f372bb958</anchor>
      <arglist>(uint16_t in_row, uint16_t in_col, uint16_t start_row, uint16_t start_col, uint16_t step_row, uint16_t step_col, uint16_t *out_row, uint16_t *out_col)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>pre_in_post_world</name>
      <anchorfile>common__kernel_8c.html</anchorfile>
      <anchor>a86920262c0a0b97f0cde9a8d05b5e12b</anchor>
      <arglist>(uint16_t in_row, uint16_t in_col, uint16_t start_row, uint16_t start_col, uint16_t step_row, uint16_t step_col, int16_t *out_row, int16_t *out_col)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>common_kernel.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>common__kernel_8h.html</filename>
    <member kind="function">
      <type>uint16_t</type>
      <name>uidiv</name>
      <anchorfile>common__kernel_8h.html</anchorfile>
      <anchor>ac7271db2d65d3c345c76024e1becfe99</anchor>
      <arglist>(uint32_t dividend, uint16_t divider, uint16_t *remainder)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>post_in_pre_world</name>
      <anchorfile>common__kernel_8h.html</anchorfile>
      <anchor>ae380e1c9722449c4ef92aa2f372bb958</anchor>
      <arglist>(uint16_t in_row, uint16_t in_col, uint16_t start_row, uint16_t start_col, uint16_t step_row, uint16_t step_col, uint16_t *out_row, uint16_t *out_col)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>pre_in_post_world</name>
      <anchorfile>common__kernel_8h.html</anchorfile>
      <anchor>a86920262c0a0b97f0cde9a8d05b5e12b</anchor>
      <arglist>(uint16_t in_row, uint16_t in_col, uint16_t start_row, uint16_t start_col, uint16_t step_row, uint16_t step_col, int16_t *out_row, int16_t *out_col)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>common_mem.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>common__mem_8h.html</filename>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>fast_memcpy</name>
      <anchorfile>common__mem_8h.html</anchorfile>
      <anchor>a293d12ada8b9ace4a1b4b19aa49df3fe</anchor>
      <arglist>(void *restrict to, const void *restrict from, size_t num_bytes)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>connection__generator_8c.html</filename>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" imported="no">connection_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" imported="no">generator_types.h</includes>
    <includes id="connection__generator__one__to__one_8h" name="connection_generator_one_to_one.h" local="yes" imported="no">connection_generators/connection_generator_one_to_one.h</includes>
    <includes id="connection__generator__all__to__all_8h" name="connection_generator_all_to_all.h" local="yes" imported="no">connection_generators/connection_generator_all_to_all.h</includes>
    <includes id="connection__generator__fixed__prob_8h" name="connection_generator_fixed_prob.h" local="yes" imported="no">connection_generators/connection_generator_fixed_prob.h</includes>
    <includes id="connection__generator__fixed__total_8h" name="connection_generator_fixed_total.h" local="yes" imported="no">connection_generators/connection_generator_fixed_total.h</includes>
    <includes id="connection__generator__fixed__pre_8h" name="connection_generator_fixed_pre.h" local="yes" imported="no">connection_generators/connection_generator_fixed_pre.h</includes>
    <includes id="connection__generator__fixed__post_8h" name="connection_generator_fixed_post.h" local="yes" imported="no">connection_generators/connection_generator_fixed_post.h</includes>
    <includes id="connection__generator__kernel_8h" name="connection_generator_kernel.h" local="yes" imported="no">connection_generators/connection_generator_kernel.h</includes>
    <class kind="struct">connection_generator_info</class>
    <class kind="struct">connection_generator</class>
    <member kind="enumvalue">
      <name>ONE_TO_ONE</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600adaccc17f840cc67d0e9c1a9a331b2fb4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ALL_TO_ALL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600a403e4025d2925f132293a50eae7381fe</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_PROBABILITY</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600a8f6a6db47b5476cf11f24317f14ee4a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_TOTAL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600a8338dcf5840ce1a01a4c26d9c49dc560</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_PRE</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600aa667dfec30c43a0320c7bd76b99bd4c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_POST</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600aa130e7b038fc0ede3b0203931063b116</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>KERNEL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600a53c6e691e7db9eceefc0fb37cb724cd2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_CONNECTION_GENERATORS</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>abed82baf7f470b522273a3e37c24c600ab1144285d7382feeb4687af0263e2467</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>connection_generator_t</type>
      <name>connection_generator_init</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>a1a3c815932172e25183bbd6c237d0974</anchor>
      <arglist>(uint32_t hash, address_t *in_region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>connection_generator_generate</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>a82fb9cd00aa5c51cdcbf97879763f28e</anchor>
      <arglist>(connection_generator_t generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>connection_generator_free</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>ab9b132e35b3d39240d34e7f225193910</anchor>
      <arglist>(connection_generator_t generator)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const connection_generator_info</type>
      <name>connection_generators</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>ab3f5298c96970f1f9b2fbf3cdadbc60f</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>connection__generator_8h.html</filename>
    <member kind="function">
      <type>connection_generator_t</type>
      <name>connection_generator_init</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>aaef4756b6809d564b87d98007f5e27a1</anchor>
      <arglist>(uint32_t hash, address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>connection_generator_free</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>ab9b132e35b3d39240d34e7f225193910</anchor>
      <arglist>(connection_generator_t generator)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>connection_generator_generate</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>a82fb9cd00aa5c51cdcbf97879763f28e</anchor>
      <arglist>(connection_generator_t generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_all_to_all.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__all__to__all_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">all_to_all</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_all_to_all_initialise</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a8d9ed83bb1525d9746415cc0006b4766</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_all_to_all_free</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a71eb137d1e03e170895b6bf705bcd0bd</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_all_to_all_generate</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>af4d7356915b9d9c671b2acaadde00d12</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_post.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__post_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <class kind="struct">fixed_post_params</class>
    <class kind="struct">fixed_post</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_post_initialise</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>af300d7d4f64b41abc443edefe98a8958</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_fixed_post_free</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>ae913507c69e31814ff266356875d0c3f</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>post_random_in_range</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>ae08cfcb6c50855844e811f8bec2eacbf</anchor>
      <arglist>(struct fixed_post *obj, uint32_t range)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_fixed_post_generate</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>ab2e91f8df6e9d90fbd9028a6ff1c0964</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_pre.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <class kind="struct">fixed_pre_params</class>
    <class kind="struct">fixed_pre</class>
    <class kind="struct">fixed_pre_globals_t</class>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>pre_random_in_range</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a54a7a66e8fd8c26ab3c07eba79adec9b</anchor>
      <arglist>(struct fixed_pre *obj, uint32_t range)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_pre_initialise</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>abe6fe758cca3bdf0ec27a3aef98d535a</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>connection_generator_fixed_pre_free</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>ac7bbf4bf4f70b6455cb935e57165a614</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>connection_generator_fixed_pre_generate</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a935e1c46d26b5ce26a6abaefc0fc004c</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static struct fixed_pre_globals_t</type>
      <name>fixed_pre_globals</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a41013d6c3210c085c7880db23bbcb53e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_prob.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__prob_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">fixed_prob_params</class>
    <class kind="struct">fixed_prob</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_prob_initialise</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>a6436406b7bd4c57206d0491c42e62f2e</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_fixed_prob_free</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>ad5ab082c89ff3e5317a09aa7f67a6442</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_fixed_prob_generate</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>a7b905731d8c7fa5fafc3dfed1992b4f5</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_total.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__total_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">fixed_total_params</class>
    <class kind="struct">fixed_total</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_total_initialise</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a97f78806add1b87f56c6c852906a7cdd</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_fixed_total_free</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a0d3e8f5ac6f3487cc51cf868f75e7619</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>binomial</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a1f0a769498290639dfc184f29e18de1c</anchor>
      <arglist>(uint32_t n, uint32_t N, uint32_t K, rng_t rng)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>hypergeom</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a081ce5ff6a9e874943fc38e9815afa34</anchor>
      <arglist>(uint32_t n, uint32_t N, uint32_t K, rng_t rng)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_fixed_total_generate</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a1c9a7660e7c8a2f2b89d837ff908e1f0</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_kernel.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__kernel_8h.html</filename>
    <includes id="common__kernel_8h" name="common_kernel.h" local="no" imported="no">synapse_expander/common_kernel.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="no" imported="no">synapse_expander/common_mem.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">kernel</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_kernel_initialise</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>ab16e17812b60db23d3d20cbfe6658bf6</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_kernel_free</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a0e3d6a7e01f6bcfe0c5f9063e879bff2</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_kernel_generate</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a12d662122a5300d729a5266a3736becf</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_one_to_one.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__one__to__one_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">one_to_one</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_one_to_one_initialise</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>aacacd3d03b90bd854ba61a48097b0e97</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_one_to_one_free</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>a519a2706ae01863c6124c8dc78a6a8a7</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>connection_generator_one_to_one_generate</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>afa595e91deb02bd7ae09d16c0cd3d1de</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>delay_expander.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>delay__expander_8c.html</filename>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" imported="no">connection_generator.h</includes>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" imported="no">param_generator.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" imported="no">matrix_generators/matrix_generator_common.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" imported="no">common_mem.h</includes>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" imported="no">delay_extension/delay_extension.h</includes>
    <class kind="struct">delay_builder_config</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_delay_builder_region</name>
      <anchorfile>delay__expander_8c.html</anchorfile>
      <anchor>ae335350371ddbd7a0c4da33ab032fcd5</anchor>
      <arglist>(address_t *in_region, bit_field_t *neuron_delay_stage_config, uint32_t pre_slice_start, uint32_t pre_slice_count)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>run_delay_expander</name>
      <anchorfile>delay__expander_8c.html</anchorfile>
      <anchor>ab8e8cac1b4ebc8d1fd0d665b9639988e</anchor>
      <arglist>(void *delay_params_address, address_t params_address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>delay__expander_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>generator_types.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>generator__types_8h.html</filename>
    <member kind="typedef">
      <type>uint32_t</type>
      <name>generator_hash_t</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a55f8d20fc9350939e3fa6a85d8aed90c</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>void *()</type>
      <name>initialize_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a2eba3e6d9fed26ac5064e720ceed0f91</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="typedef">
      <type>void()</type>
      <name>free_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a6b16387baa51e7bff16f0e21220c254e</anchor>
      <arglist>(void *data)</arglist>
    </member>
    <member kind="typedef">
      <type>uint32_t()</type>
      <name>generate_connection_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a074270ea0663c44b9bcc392c1fcb935e</anchor>
      <arglist>(void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count, uint32_t pre_neuron_index, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices)</arglist>
    </member>
    <member kind="typedef">
      <type>void()</type>
      <name>generate_param_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a776082247e99447649d185bdd6b8f777</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
    <member kind="typedef">
      <type>void()</type>
      <name>generate_row_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a8d1b332d6f35a47155fc48aabebeaf80</anchor>
      <arglist>(void *generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t n_pre_neurons, uint32_t pre_neuron_index, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t synapse_type_bits, uint32_t synapse_index_bits, uint32_t synapse_type, uint32_t n_synapses, uint16_t *indices, uint16_t *delays, uint16_t *weights, uint32_t max_stage, uint32_t max_delay_in_a_stage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>matrix__generator_8c.html</filename>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" imported="no">matrix_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" imported="no">generator_types.h</includes>
    <includes id="matrix__generator__static_8h" name="matrix_generator_static.h" local="yes" imported="no">matrix_generators/matrix_generator_static.h</includes>
    <includes id="matrix__generator__stdp_8h" name="matrix_generator_stdp.h" local="yes" imported="no">matrix_generators/matrix_generator_stdp.h</includes>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" imported="no">delay_extension/delay_extension.h</includes>
    <class kind="struct">matrix_generator_info</class>
    <class kind="struct">matrix_generator</class>
    <member kind="enumvalue">
      <name>STATIC_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>ab04a0655cd1e3bcac5e8f48c18df1a57af14f18f5ed2665f8cb095c1363fc9848</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PLASTIC_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>ab04a0655cd1e3bcac5e8f48c18df1a57a08b27fbab7a770bae071d9defb278782</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_MATRIX_GENERATORS</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>ab04a0655cd1e3bcac5e8f48c18df1a57aba9a03e4fd023b2837469ea1ff6225a3</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>matrix_generator_t</type>
      <name>matrix_generator_init</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a9539b11486e767ca5114db0390a505a1</anchor>
      <arglist>(uint32_t hash, address_t *in_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_free</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>aafbab40316b9861d41999287c65d1dbe</anchor>
      <arglist>(matrix_generator_t generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>matrix_generator_write_row</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a94ef2f50254210f92e2d2ea5d85c486d</anchor>
      <arglist>(matrix_generator_t generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t n_pre_neurons, uint32_t pre_neuron_index, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits, uint32_t synapse_type, uint32_t n_synapses, uint16_t *indices, uint16_t *delays, uint16_t *weights, uint32_t max_stage, uint32_t max_delay_per_stage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>rescale_delay</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>abe727a061d0165e4205bb2764711e760</anchor>
      <arglist>(accum delay, accum timestep_per_delay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>rescale_weight</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a5ee0662d7b826e8ba7abfa68bbe6a327</anchor>
      <arglist>(accum weight, unsigned long accum weight_scale)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>matrix_generator_generate</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a0830f8d698bd7251d62c094a41d9d160</anchor>
      <arglist>(matrix_generator_t generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t max_row_n_synapses, uint32_t max_delayed_row_n_synapses, uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits, uint32_t synapse_type, unsigned long accum *weight_scales, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t pre_slice_start, uint32_t pre_slice_count, connection_generator_t connection_generator, param_generator_t delay_generator, param_generator_t weight_generator, uint32_t max_stage, uint32_t max_delay_in_a_stage, accum timestep_per_delay)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const struct matrix_generator_info</type>
      <name>matrix_generators</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a420abd8627e0860d1b5e902686806ea0</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>matrix__generator_8h.html</filename>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" imported="no">connection_generator.h</includes>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" imported="no">param_generator.h</includes>
    <member kind="function">
      <type>matrix_generator_t</type>
      <name>matrix_generator_init</name>
      <anchorfile>matrix__generator_8h.html</anchorfile>
      <anchor>a2ad0747490f9e777226c0508f7c670af</anchor>
      <arglist>(uint32_t hash, address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_free</name>
      <anchorfile>matrix__generator_8h.html</anchorfile>
      <anchor>aafbab40316b9861d41999287c65d1dbe</anchor>
      <arglist>(matrix_generator_t generator)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>matrix_generator_generate</name>
      <anchorfile>matrix__generator_8h.html</anchorfile>
      <anchor>a3a75ff58588bafc87d46b933290ba3e1</anchor>
      <arglist>(matrix_generator_t generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t max_row_n_synapses, uint32_t max_delayed_row_n_synapses, uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits, uint32_t synapse_type, unsigned long accum *weight_scales, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t pre_slice_start, uint32_t pre_slice_count, connection_generator_t connection_generator, param_generator_t delay_generator, param_generator_t weight_generator, uint32_t max_stage, uint32_t max_delay_per_stage, accum timestep_per_delay)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_common.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__common_8h.html</filename>
    <class kind="struct">delay_value</class>
    <member kind="function" static="yes">
      <type>static struct delay_value</type>
      <name>get_delay</name>
      <anchorfile>matrix__generator__common_8h.html</anchorfile>
      <anchor>a70d02afe8081b6ed99856fe4594e88e8</anchor>
      <arglist>(uint16_t delay_value, uint32_t max_stage, uint32_t max_delay_per_stage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_static.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__static_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" imported="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" imported="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">static_row_t</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_WEIGHT_SHIFT</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a694a022e33e33cf62ed968fc3e61bfcd</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_WEIGHT_MASK</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a5ac88042b75ba0f76e04ce5c830ec838</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_DELAY_MASK</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a9932d3e682ca42eb572c28a676e4e4b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>matrix_generator_static_initialize</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a34e736f14eb0b8aa28b50e8b1d053acf</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>matrix_generator_static_free</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a21c6ce388b821caaa1268c3d6abb9ef1</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>build_static_word</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>abef0ba0fc1675b818c5385bb2e99aafa</anchor>
      <arglist>(uint16_t weight, uint16_t delay, uint32_t type, uint16_t post_index, uint32_t synapse_type_bits, uint32_t synapse_index_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>matrix_generator_static_write_row</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a03d500a7b238275b5b5a32fd32ff6f80</anchor>
      <arglist>(void *generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t n_pre_neurons, uint32_t pre_neuron_index, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t synapse_type_bits, uint32_t synapse_index_bits, uint32_t synapse_type, uint32_t n_synapses, uint16_t *indices, uint16_t *delays, uint16_t *weights, uint32_t max_stage, uint32_t max_delay_per_stage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_stdp.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__stdp_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" imported="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" imported="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">row_plastic_t</class>
    <class kind="struct">row_fixed_t</class>
    <class kind="struct">matrix_generator_stdp</class>
    <member kind="define">
      <type>#define</type>
      <name>SYNAPSE_DELAY_MASK</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a9932d3e682ca42eb572c28a676e4e4b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>void *</type>
      <name>matrix_generator_stdp_initialize</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a0ddb143edd7818571ecf6ccb2d22abb9</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_stdp_free</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aa0ccbf6127b7bd9ba00efc3ba17373e9</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>build_fixed_plastic_half_word</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a011bc952ba061982959d524e9fbd68cc</anchor>
      <arglist>(uint16_t delay, uint32_t type, uint32_t post_index, uint32_t synapse_type_bits, uint32_t synapse_index_bits)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_stdp_write_row</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a7e08d07102afbb52373e761318380e97</anchor>
      <arglist>(void *generator, address_t synaptic_matrix, address_t delayed_synaptic_matrix, uint32_t n_pre_neurons, uint32_t pre_neuron_index, uint32_t max_row_n_words, uint32_t max_delayed_row_n_words, uint32_t synapse_type_bits, uint32_t synapse_index_bits, uint32_t synapse_type, uint32_t n_synapses, uint16_t *indices, uint16_t *delays, uint16_t *weights, uint32_t max_stage, uint32_t max_delay_per_stage)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>param__generator_8c.html</filename>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" imported="no">param_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" imported="no">generator_types.h</includes>
    <includes id="param__generator__constant_8h" name="param_generator_constant.h" local="yes" imported="no">param_generators/param_generator_constant.h</includes>
    <includes id="param__generator__uniform_8h" name="param_generator_uniform.h" local="yes" imported="no">param_generators/param_generator_uniform.h</includes>
    <includes id="param__generator__normal_8h" name="param_generator_normal.h" local="yes" imported="no">param_generators/param_generator_normal.h</includes>
    <includes id="param__generator__normal__clipped_8h" name="param_generator_normal_clipped.h" local="yes" imported="no">param_generators/param_generator_normal_clipped.h</includes>
    <includes id="param__generator__normal__clipped__to__boundary_8h" name="param_generator_normal_clipped_to_boundary.h" local="yes" imported="no">param_generators/param_generator_normal_clipped_to_boundary.h</includes>
    <includes id="param__generator__exponential_8h" name="param_generator_exponential.h" local="yes" imported="no">param_generators/param_generator_exponential.h</includes>
    <includes id="param__generator__kernel_8h" name="param_generator_kernel.h" local="yes" imported="no">param_generators/param_generator_kernel.h</includes>
    <class kind="struct">param_generator_info</class>
    <class kind="struct">param_generator</class>
    <member kind="enumvalue">
      <name>CONSTANT</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388a83972670b57415508523b5641bb46116</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>UNIFORM</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388a8f44784d154005a214e0fe94119d28ef</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388a50d1448013c6f17125caee18aa418af7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL_CLIPPED</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388ac40cefd2a096660da3f41d6ee6352889</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL_CLIPPED_BOUNDARY</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388aca06c44d4221f47f9d61534ca1e35752</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXPONENTIAL</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388aa6055a3a8ab1aed0594419b51d9ec15e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>KERNEL</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388a53c6e691e7db9eceefc0fb37cb724cd2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_PARAM_GENERATORS</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a385c44f6fb256e5716a2302a5b940388ab8047ff7dfdb2c76ef1e78a7e6347777</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>param_generator_t</type>
      <name>param_generator_init</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>ae52a45690f00dfe7384a14645b3512de</anchor>
      <arglist>(uint32_t hash, address_t *in_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>param_generator_generate</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>ae85e6c376848da24228c97141d0d2027</anchor>
      <arglist>(param_generator_t generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>param_generator_free</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a20b9f761fb073750e083d131cf49812e</anchor>
      <arglist>(param_generator_t generator)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const struct param_generator_info</type>
      <name>param_generators</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>ace4d5547ba44f140e4eb0e5f6fe1a0cc</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>param__generator_8h.html</filename>
    <member kind="function">
      <type>param_generator_t</type>
      <name>param_generator_init</name>
      <anchorfile>param__generator_8h.html</anchorfile>
      <anchor>a7f47aef417cd5ec8cf73a199d71dced2</anchor>
      <arglist>(uint32_t hash, address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>param_generator_generate</name>
      <anchorfile>param__generator_8h.html</anchorfile>
      <anchor>ae85e6c376848da24228c97141d0d2027</anchor>
      <arglist>(param_generator_t generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>param_generator_free</name>
      <anchorfile>param__generator_8h.html</anchorfile>
      <anchor>a20b9f761fb073750e083d131cf49812e</anchor>
      <arglist>(param_generator_t generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_constant.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__constant_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_constant</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_constant_initialize</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>a52720c983e24979540f5cf27d02b0c14</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_constant_free</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>ae74a9c20cfc678e6ddd497a11385af04</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_constant_generate</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>a22265a38730d1027e422da52c55b1925</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_exponential.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__exponential_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_exponential_params</class>
    <class kind="struct">param_generator_exponential</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_exponential_initialize</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a518b5f87123dff22dbf32caeebf3bd62</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_exponential_free</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a5e6bcf3faf8c177cd11b9aa85f8332ab</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_exponential_generate</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a35c790b036e9fe9d1fa56d6f73481253</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_kernel.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__kernel_8h.html</filename>
    <includes id="common__kernel_8h" name="common_kernel.h" local="no" imported="no">synapse_expander/common_kernel.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="no" imported="no">synapse_expander/common_mem.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_kernel</class>
    <class kind="struct">all_kernel_params</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_kernel_initialize</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a39733ff7b8e93862022624d1677e64d2</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_kernel_free</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a0e39efa09a5e7eaf0d1176854c932da0</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_kernel_generate</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>ae8923c53570bb39fb37da751c4bc54e9</anchor>
      <arglist>(void *generator, uint32_t n_synapses, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">normal_params</class>
    <class kind="struct">param_generator_normal</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_normal_initialize</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>ae437fca279630eb531de2055d33384d8</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_free</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>a5da899810d276b0a718b0802fb176783</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_generate</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>aab67db27d60f95cb89f416f5437337fa</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal_clipped.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal__clipped_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">normal_clipped_params</class>
    <class kind="struct">param_generator_normal_clipped</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_REDRAWS</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>a47fa28c0ff86570b51eb712e1c37a9bd</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_normal_clipped_initialize</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>a2e7a19b44cf70f55ce523967c2ebe963</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_free</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>aa9c765cadcfd29badb3aa2b96aa6ace2</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_generate</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>aee9da23a6c9386207ef4aa389c193465</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal_clipped_to_boundary.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal__clipped__to__boundary_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">normal_clipped_boundary_params</class>
    <class kind="struct">param_generator_normal_clipped_boundary</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_normal_clipped_boundary_initialize</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>aea1249b5291999b5c20957a84794d52f</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_boundary_free</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>a5da6f0676e55afbd36f5a0922c5c33f9</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_boundary_generate</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>a4fc1e0ce8a65ceece5bd4692dfc3571f</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_uniform.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/param_generators/</path>
    <filename>param__generator__uniform_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" imported="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" imported="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">uniform_params</class>
    <class kind="struct">param_generator_uniform</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_uniform_initialize</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>aa98cee205ae39374662b092fc83c7f43</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_uniform_free</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>a445a600b3abdfaa44355db5151482756</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_uniform_generate</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>ae052c5aefd98b10fb363a5baf6ba0b00</anchor>
      <arglist>(void *generator, uint32_t n_indices, uint32_t pre_neuron_index, uint16_t *indices, accum *values)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>rng.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>rng_8c.html</filename>
    <includes id="rng_8h" name="rng.h" local="yes" imported="no">rng.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" imported="no">common_mem.h</includes>
    <class kind="struct">rng</class>
    <member kind="function">
      <type>rng_t</type>
      <name>rng_init</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>ac2b523470897c3c3e4168e8d82579d18</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>rng_generator</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>aa3c7d931977e162864cb4615442d96b7</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_exponential</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>a12e0ea48f3cf6181063f30ece7b30c2d</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_normal</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>a7afddf66f0bcc73ecd2637231a654f01</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>rng_free</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>a469702c3bba13b63ccfba049840500d8</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>rng.h</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>rng_8h.html</filename>
    <member kind="function">
      <type>rng_t</type>
      <name>rng_init</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>ac2b523470897c3c3e4168e8d82579d18</anchor>
      <arglist>(address_t *region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>rng_generator</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>aa3c7d931977e162864cb4615442d96b7</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_exponential</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a12e0ea48f3cf6181063f30ece7b30c2d</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_normal</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a7afddf66f0bcc73ecd2637231a654f01</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>rng_free</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a469702c3bba13b63ccfba049840500d8</anchor>
      <arglist>(rng_t rng)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_expander.c</name>
    <path>/github/workspace/neural_modelling/src/synapse_expander/</path>
    <filename>synapse__expander_8c.html</filename>
    <includes id="regions_8h" name="regions.h" local="no" imported="no">neuron/regions.h</includes>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" imported="no">matrix_generator.h</includes>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" imported="no">connection_generator.h</includes>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" imported="no">param_generator.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" imported="no">common_mem.h</includes>
    <class kind="struct">connection_builder_config</class>
    <class kind="struct">expander_config</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_connection_builder_region</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>aa6bfc8d65fe33be9e28e4c0f18cd554b</anchor>
      <arglist>(address_t *in_region, address_t synaptic_matrix_region, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits, unsigned long accum *weight_scales)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>run_synapse_expander</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>ab2b96fb3f7cddc88c3b12263c25f0fc1</anchor>
      <arglist>(address_t params_address, address_t synaptic_matrix_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>additional_input_t</name>
    <filename>additional__input__none__impl_8h.html</filename>
    <anchor>structadditional__input__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>exp_TauCa</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a0c1f083f2abaa9a200f9bc6e26ccbb92</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>I_Ca2</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>afd249bff7976a52de9117b84aea37673</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>I_alpha</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a3099dc9d6b59766d49d803f62b22a5c5</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>additive_one_term_config_t</name>
    <filename>weight__additive__one__term__impl_8c.html</filename>
    <anchor>structadditive__one__term__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>additive_two_term_config_t</name>
    <filename>weight__additive__two__term__impl_8c.html</filename>
    <anchor>structadditive__two__term__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>address_and_row_length</name>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <anchor>structaddress__and__row__length</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>row_length</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1fb46843c73b7998401310d379339f64</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a05b647c59b38ca2dc9eff3b953972630</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>is_single</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>abf7a35a5644b46e2db354540b8190f33</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>address_list_entry</name>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <anchor>unionaddress__list__entry</anchor>
  </compound>
  <compound kind="struct">
    <name>all_kernel_params</name>
    <filename>param__generator__kernel_8h.html</filename>
    <anchor>structall__kernel__params</anchor>
    <member kind="variable">
      <type>struct param_generator_kernel</type>
      <name>params</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a40993390d517d0a66144fd5d36523f57</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum *</type>
      <name>values</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>aa55383a91c659f798dc4faf98cfd18ea</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>all_to_all</name>
    <filename>connection__generator__all__to__all_8h.html</filename>
    <anchor>structall__to__all</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pre_lo</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a9323154e7036f6d2d04d52e15583b768</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pre_hi</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>aab410956d63d1b75a41c9a279ff197b5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_lo</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a5a42da71ba22ccc58cd2022154ef8df1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_hi</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a3f5deb2e9413e5ae2e0bca1ba02e3744</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>alpha_params_t</name>
    <filename>synapse__types__alpha__impl_8h.html</filename>
    <anchor>structalpha__params__t</anchor>
    <member kind="variable">
      <type>input_t</type>
      <name>lin_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a2b42cfcc4ba66835e143e623afdc99d6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exp_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a21fdb5217753bcf2c3d00f3c8d691189</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>dt_divided_by_tau_sqr</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a302d76f88428da70bcddb6d6eae4d078</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>decay_t</type>
      <name>decay</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>af030e3f5a4c54671849dfe95356671a8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>q_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>aef39e3e4d64c69ee81da23a792c42e11</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>bitfield_info_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structbitfield__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>bitfield_values_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structbitfield__values__t</anchor>
  </compound>
  <compound kind="struct">
    <name>builder_region_struct</name>
    <filename>bit__field__expander_8c.html</filename>
    <anchor>structbuilder__region__struct</anchor>
    <member kind="variable">
      <type>int</type>
      <name>master_pop_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a6cc1f10fa0516c89cf9fe5c6f681f9a6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>synaptic_matrix_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a1eb0a2251b321c5b7dae43b2df8a5148</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>direct_matrix_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a9a9c911f0c498e2e9f83c9a08580dd11</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>bit_field_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a9f1f0eb2d9f6b0f31c7c71359e5d42a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>bit_field_key_map_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>a80165df779a65726efc433467d5bc955</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>structural_matrix_region_id</name>
      <anchorfile>bit__field__expander_8c.html</anchorfile>
      <anchor>ae58e2079031afe22e9e02100fab9fbb4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>connection_builder_config</name>
    <filename>synapse__expander_8c.html</filename>
    <anchor>structconnection__builder__config</anchor>
  </compound>
  <compound kind="struct">
    <name>connection_generator_info</name>
    <filename>connection__generator_8c.html</filename>
    <anchor>structconnection__generator__info</anchor>
    <member kind="variable">
      <type>generator_hash_t</type>
      <name>hash</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>ac546f0ebffe9fa2e64d2b822297511b1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>initialize_func *</type>
      <name>initialize</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aa84452ef3f1cb97053d14af2570129b5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>generate_connection_func *</type>
      <name>generate</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>ac02a18c2c72affcf44c2166cab070a84</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>free_func *</type>
      <name>free</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>ab5116cf03d5a141b805d248bb609e9b1</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>connection_generator</name>
    <filename>connection__generator_8c.html</filename>
    <anchor>structconnection__generator</anchor>
  </compound>
  <compound kind="struct">
    <name>current_state_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structcurrent__state__t</anchor>
    <member kind="variable">
      <type>mars_kiss64_seed_t *</type>
      <name>local_seed</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a95fc96bd4899b31f5950f74e458fcba2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_low_atom</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a45fd8cc8643c292363b09acdb024b5a6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>element_exists</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a31353ee4e32638f42f20e496de037453</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>offset</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a04d6f648c9fbb4c183c041ce6444b07d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>delay</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>ac2d5306d2023cbb2fb5993e24ead4dd6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>weight</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a8588f5e975650a2c0d118818575c6b2a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type</name>
      <anchorfile>sp__structs_8h.html</anchorfile>
      <anchor>a3f02cf224adbd87ab374eff348ac8b3a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>delay_builder_config</name>
    <filename>delay__expander_8c.html</filename>
    <anchor>structdelay__builder__config</anchor>
  </compound>
  <compound kind="struct">
    <name>delay_extension_provenance</name>
    <filename>delay__extension_8c.html</filename>
    <anchor>structdelay__extension__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_received</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a69b8bd9382be92bf6854dc5f921ee317</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_processed</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a1adc1b0e109a817205eecc7fe26b14e4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_added</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>acbaa257f6e6e932abf4010eba0deae93</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_sent</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a859939d1c299e24a68bb25e7af803895</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_buffer_overflows</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a14402f68e6fb5f758c453cd1ef86f954</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_delays</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a3ca931b66220774b3aaf1dea3db2b392</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>times_tdma_fell_behind</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a91449b33fd2d1a77fac263c2de918e29</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_lost_due_to_count_saturation</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aac3499d38dafe99c13b7f0f373dae57d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_dropped_due_to_invalid_neuron_value</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a42963fa621bbc30f989a6ca372780c86</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_dropped_due_to_invalid_key</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a1dce1d90e3a85858e234dda0be1c229b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count_input_buffer_packets_late</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ad66252e46fee6d3abdb2071f548532c5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_backgrounds_queued</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aca8046fc67baa1fe980be61d07096396</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_background_queue_overloads</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>aa6f8cf72b9fbed71a4cd0989050ef04d</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>delay_parameters</name>
    <filename>delay__extension_8h.html</filename>
    <anchor>structdelay__parameters</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>has_key</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6ed0cc408a479fad7dc7b01114816aa7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a91062442bc8f2d51d439f6a28c10956c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>incoming_key</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a5ee91b451859232bf69b98d8fe5efeed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>incoming_mask</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e62350e8d45d7f40dd19e685a06891f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_atoms</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a9e45122a1ce77599d6fd04118ddfd33b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_delay_stages</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>ae066739d171e52ac2fa7001f58891b42</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_delay_in_a_stage</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a834003ce931356a849f561dcd7fa2960</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>clear_packets</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a419319f82ec1b09d73f76ef2a298eef9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delay_blocks</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>ac96e823ff8133a64c9cdc218b44244aa</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>delay_value</name>
    <filename>matrix__generator__common_8h.html</filename>
    <anchor>structdelay__value</anchor>
  </compound>
  <compound kind="struct">
    <name>delta_params_t</name>
    <filename>synapse__types__delta__impl_8h.html</filename>
    <anchor>structdelta__params__t</anchor>
    <member kind="variable">
      <type>input_t</type>
      <name>synaptic_input_value</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a338e5d451991384eced053db6a2b7942</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>direct_matrix_data_t</name>
    <filename>direct__synapses_8c.html</filename>
    <anchor>structdirect__matrix__data__t</anchor>
    <member kind="variable">
      <type>const uint32_t</type>
      <name>size</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a7b6f1aa45c96e6dfe18c9863ced8982a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const uint32_t</type>
      <name>data</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>acd4af094bcf79182ea98ef2185bf5568</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>dma_buffer</name>
    <filename>spike__processing_8c.html</filename>
    <anchor>structdma__buffer</anchor>
    <member kind="variable">
      <type>synaptic_row_t</type>
      <name>sdram_writeback_address</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a7663f1eea61dda1540ac1a8641040d0b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>spike_t</type>
      <name>originating_spike</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a3513c98a97e75598a54b33dcde34a12c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_bytes_transferred</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a764511923c4c18e2c1303c4386aaf5e3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>synaptic_row_t</type>
      <name>row</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a654a0761ac493ec478a88f2e266be543</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>dual_fsm_config_t</name>
    <filename>timing__recurrent__dual__fsm__impl_8c.html</filename>
    <anchor>structdual__fsm__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>elimination_params</name>
    <filename>elimination__random__by__weight__impl_8h.html</filename>
    <anchor>structelimination__params</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prob_elim_depression</name>
      <anchorfile>elimination__random__by__weight__impl_8h.html</anchorfile>
      <anchor>a310e86509235bf6cc5a88320fb4bda33</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prob_elim_potentiation</name>
      <anchorfile>elimination__random__by__weight__impl_8h.html</anchorfile>
      <anchor>a3f68d540a481bf623e8b3dd63a2964ac</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>threshold</name>
      <anchorfile>elimination__random__by__weight__impl_8h.html</anchorfile>
      <anchor>ac942fdef1571e0cbf6504372f011b977</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>exp_params_t</name>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <anchor>structexp__params__t</anchor>
    <member kind="variable">
      <type>decay_t</type>
      <name>decay</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>aacee2e1a8db0f17984b2f3e4c42e7ee6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>decay_t</type>
      <name>init</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>aaa23e193beba47e2f10741bffe80b786</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>synaptic_input_value</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac8b591da2d0dfcbcb814dbf8580cbd56</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>expander_config</name>
    <filename>synapse__expander_8c.html</filename>
    <anchor>structexpander__config</anchor>
  </compound>
  <compound kind="struct">
    <name>extra_info</name>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <anchor>structextra__info</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>core_mask</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac028589ad82b326aa64c8f71d8650c6a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_words</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a30fce9306ac45fadef4dd737d177d467</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask_shift</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ad3098b05fff6bb47f13fe6f9cf975414</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_neurons</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>aa4dfc64a68bcb1cf34110d310f67530c</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>fixed_post</name>
    <filename>connection__generator__fixed__post_8h.html</filename>
    <anchor>structfixed__post</anchor>
    <member kind="variable">
      <type>struct fixed_post_params</type>
      <name>params</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a8ed1e9dc57252dc7895cc4922ae38687</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rng_t</type>
      <name>rng</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a1555dd530c7395bb4373b6bb5b699297</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>fixed_post_params</name>
    <filename>connection__generator__fixed__post_8h.html</filename>
    <anchor>structfixed__post__params</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pre_lo</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a4eb03d0f757266d94efef44867b62729</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pre_hi</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a8804d98e8134803269a43f1b560230fc</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_lo</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>aab9411033f2f70c87c42301cf42fff13</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_hi</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a6cc17ffc0a60395bf1697e96ba776d52</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>allow_self_connections</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a9f473a5b1550bc9c4e4fa5686eacfef0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>with_replacement</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>ad2798146758f40c69bffa640909166ad</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_post</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>af4c0ed8a643a617c21ce2a377fd1952c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_post_neurons</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a19ed05dac833a17b29f0c53d918bd1d2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>fixed_pre</name>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <anchor>structfixed__pre</anchor>
  </compound>
  <compound kind="struct">
    <name>fixed_pre_globals_t</name>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <anchor>structfixed__pre__globals__t</anchor>
    <member kind="variable">
      <type>void *</type>
      <name>full_indices</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a9b06d08a35c06fc8558f75338b113065</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_neurons_done</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a39a9876a13a2fe1e6700d4fa144de305</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bool</type>
      <name>in_sdram</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a466a132ae35d326ff7de39154149e91d</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>fixed_pre_params</name>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <anchor>structfixed__pre__params</anchor>
  </compound>
  <compound kind="struct">
    <name>fixed_prob</name>
    <filename>connection__generator__fixed__prob_8h.html</filename>
    <anchor>structfixed__prob</anchor>
  </compound>
  <compound kind="struct">
    <name>fixed_prob_params</name>
    <filename>connection__generator__fixed__prob_8h.html</filename>
    <anchor>structfixed__prob__params</anchor>
  </compound>
  <compound kind="struct">
    <name>fixed_total</name>
    <filename>connection__generator__fixed__total_8h.html</filename>
    <anchor>structfixed__total</anchor>
  </compound>
  <compound kind="struct">
    <name>fixed_total_params</name>
    <filename>connection__generator__fixed__total_8h.html</filename>
    <anchor>structfixed__total__params</anchor>
  </compound>
  <compound kind="struct">
    <name>formation_params</name>
    <filename>formation__distance__dependent__impl_8h.html</filename>
    <anchor>structformation__params</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>grid_x</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a4cc7f4da55e2fba7b0f12d0b1856f90a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>grid_y</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a1bb0a8d3a12b2bc16b2f00d7e6b54b4f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>unsigned long fract</type>
      <name>grid_x_recip</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a36308a64f1768104aa73dd155c05a87b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>unsigned long fract</type>
      <name>grid_y_recip</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a5e8b9fd4addaadfef9a0604acf4ea8c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>ff_prob_size</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>abf338e53b58fbf637112ba228bd58108</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>lat_prob_size</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>af933dfda1a48600061f921ce9dded526</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>prob_tables</name>
      <anchorfile>formation__distance__dependent__impl_8h.html</anchorfile>
      <anchor>a80e302251d567088aa6ce5dc29ebbf81</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>global_neuron_params_t</name>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <anchor>structglobal__neuron__params__t</anchor>
  </compound>
  <compound kind="struct">
    <name>global_parameters</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structglobal__parameters</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>has_key</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>af0d05f9a4857217ecc6919484c6f877d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa6b9e979acf123b1713136e5931c3b78</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>set_rate_neuron_id_mask</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab4adadbc1d477b4c51e123cf3a454d26</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UFRACT</type>
      <name>seconds_per_tick</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ae0f9eec779642b68ca81ade1b1d1ce10</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>ticks_per_second</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6725343f8032eb0ad9d37408b92dace8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>slow_rate_per_tick_cutoff</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a8fc7a576f718c19bb241c4c6301fd416</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>fast_rate_per_tick_cutoff</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>afd5bbf1b89c098c3f2bf38a4689f42ba</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>first_source_id</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a4459890055b76bb63c4bd4b9ac2a14e5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spike_sources</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>afb9733b9bd7b0e69c4734ab031561139</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>mars_kiss64_seed_t</type>
      <name>spike_source_seed</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b27dd1091ed50b78407f2c69fb35582</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>input_type_t</name>
    <filename>input__type__none_8h.html</filename>
    <anchor>structinput__type__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rev_E</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>ace17cbedca27bd81e3e9d7fd6c6fe774</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rev_I</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>aab156892eda9d422b7d1dd8dfc7b979e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>int16_lut</name>
    <filename>maths_8h.html</filename>
    <anchor>structint16__lut</anchor>
    <member kind="variable">
      <type>uint16_t</type>
      <name>size</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>ab6d1fb27d517365483fc4a8fcb16b598</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>shift</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a98d5cfbb988f03dac634156f7dcdc2d7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_t</type>
      <name>values</name>
      <anchorfile>maths_8h.html</anchorfile>
      <anchor>a17b6c0ddd56ccaec45d3191da3f1c209</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>kernel</name>
    <filename>connection__generator__kernel_8h.html</filename>
    <anchor>structkernel</anchor>
    <member kind="variable">
      <type>uint16_t</type>
      <name>preWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a29bbc112113d357a62037221bf60d391</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>preHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a92644d3e86f3ac2f6852cd6b70127bbe</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>postWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a977965e46e041568151ebe05c43d4e12</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>postHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>af4fbbd46e0af5ec22281077d30b109e4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPreWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a5001c6fc9fc52779e16b25a1de8312c4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPreHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a52b8df81098000999cd06bdf716f0605</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPostWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a08e1f5da2212a2c4c3f0652f84c06935</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPostHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a3214c4ec9e3499ae1da6c775ff9dd6d8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPreWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a844f6edb27780423874a33fe54cbe811</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPreHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a7d8794e227dc4ed2c5e7867c783474c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPostWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>ab21488cf9c9cb5b4f8d030311288afe4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPostHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a32d8bdeab149cad8046a7e1f4f0f4943</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>kernelWidth</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>ad4ae6eb3b90878e1fe1ec5b565690e0b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>kernelHeight</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a6e62b50597cf2d546f6d88836e0d57e2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>key_atom_info_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structkey__atom__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>master_population_table_entry</name>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <anchor>structmaster__population__table__entry</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0afdbef67c9cba4231a9c8cc63e0c005</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a5d5364d69a3eb267eba9b0e47ffd1db7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>start</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>afb309e71903c16b95d149973e753b490</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>extra_info_flag</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a12b8d8e12253bc56e1bbd8581ad3da81</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1b52e9a32daa7fddff954e66cbd3bd4e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_generator_info</name>
    <filename>matrix__generator_8c.html</filename>
    <anchor>structmatrix__generator__info</anchor>
    <member kind="variable">
      <type>generator_hash_t</type>
      <name>hash</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a8333d4c3400688570254a1535e918b20</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>initialize_func *</type>
      <name>initialize</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>af736a8d5f4b9f65470cf1cd338ed4391</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>generate_row_func *</type>
      <name>write_row</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a7c885850d9bd6f81b8940ee96a48f3db</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>free_func *</type>
      <name>free</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>aa732cf0409128b2a144d54cf7733c756</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_generator_stdp</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>structmatrix__generator__stdp</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_half_words_per_pp_row_header</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aa5737732096b5f67fca029d1f2aed44c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_half_words_per_pp_synapse</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ab29da34a8c2311993638cb6a258d1b4a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>weight_half_word</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ac7ef0134f0184dc3c7819ab29f022bbb</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_generator</name>
    <filename>matrix__generator_8c.html</filename>
    <anchor>structmatrix__generator</anchor>
  </compound>
  <compound kind="struct">
    <name>motor_control_config_t</name>
    <filename>robot__motor__control_8c.html</filename>
    <anchor>structmotor__control__config__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>aa5e6af92fda118d10cfc4d1b691c6989</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>speed</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>ac9ed2b5461fb2fb0b3de7b25ab1e6ed4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>sample_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>aba1b565c6070a825b676abb5e5b7b77c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>update_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>af91db5a416282fefdb525fadbc6f5f8f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delay_time</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a9143eeee1ab2ee38cca77ac8ec5770b3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>delta_threshold</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a83d48617dbfa4c4c34cd8c0b58fe56b6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>continue_if_not_different</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>a545151226a39297f19f3d8b8744d29e4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>multicast_packet</name>
    <filename>munich__protocol_8h.html</filename>
    <anchor>structmulticast__packet</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>af5492aa5a4cea4a256d88d82fe7e6f4e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>payload</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a5e71d859cea4c79625e4738a5f8113f4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>payload_flag</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a8a82db9be5294fc0cf7ff5fe241d8b7c</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>multiplicative_config_t</name>
    <filename>weight__multiplicative__impl_8c.html</filename>
    <anchor>structmultiplicative__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>munich_key_bitfields_t</name>
    <filename>munich__protocol_8h.html</filename>
    <anchor>structmunich__key__bitfields__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>device</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>adbc3297c6b342ffff16c276b3d8f44d7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>payload_format</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a9923e847eb15caa2f0eb51c7e763901e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>instruction</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>af88a58a15f4007a2629456b02fa89685</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>instance_key</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>af7733652e8cf2dc7a581b66b432ab4c9</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>munich_key_t</name>
    <filename>munich__protocol_8h.html</filename>
    <anchor>unionmunich__key__t</anchor>
    <member kind="variable">
      <type>munich_key_bitfields_t</type>
      <name>bitfields</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>a69c84edcf35be44406679d226d994c32</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>value</name>
      <anchorfile>munich__protocol_8h.html</anchorfile>
      <anchor>ae25a937e1086e1ccf5579cdbe4764743</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_parameters</name>
    <filename>neuron_8c.html</filename>
    <anchor>structneuron__parameters</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_t</name>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <anchor>structneuron__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>I_offset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>af3312785809b054f13aeba3e3c2f000a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>this_h</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a36618067ab7503cd84fcf76e9e9a1111</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_membrane</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a86bb63a4a0e56518c44af0beefe8ac31</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rest</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a0448414012bd86a39307aa97378ca8f2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>R_membrane</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>aea78ba2caa325540d8571d35eba56b13</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>exp_TC</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ae86326c508ef052f75103f8fec5dff82</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>refract_timer</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>acf084ec01328ebc9b41115c053dff303</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_reset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ad64e3dbdebb524738dac569369fcb146</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>T_refract</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a960606546b094d62a8509eea60bd3dc2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_provenance</name>
    <filename>c__main_8c.html</filename>
    <anchor>structneuron__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_synaptic_events</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aa5cc7c82313ba8fd9b9300b36b5fbbcf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_synaptic_weight_saturations</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a97349e60345fc7fda140ab5ba383f661</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_input_buffer_overflows</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a26034589834a6dbf7abfbef4099f7680</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>current_timer_tick</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a7971d970224cbcc61d40e13ebd0139cb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_plastic_synaptic_weight_saturations</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a34c76b30af43caf5fc2f6db950458766</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_rewires</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ac525fc32eb7e2f1ef173901fb8dac16d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_tdma_mises</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a9567e9ef2fd91cdd106404ec2e2ed282</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_backgrounds_queued</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ab5ee7e0c23a7078a25cce1324aaeba64</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_background_queue_overloads</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ac78a4fc6fd2e44b01c34688b09a76f89</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_recording_header_t</name>
    <filename>neuron__recording_8c.html</filename>
    <anchor>structneuron__recording__header__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_recorded_vars</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>abedd25f4658e60246836b650b8432a7b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_bitfield_vars</name>
      <anchorfile>neuron__recording_8c.html</anchorfile>
      <anchor>aceb45219931c687ba2595c66b9561e18</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>normal_clipped_boundary_params</name>
    <filename>param__generator__normal__clipped__to__boundary_8h.html</filename>
    <anchor>structnormal__clipped__boundary__params</anchor>
  </compound>
  <compound kind="struct">
    <name>normal_clipped_params</name>
    <filename>param__generator__normal__clipped_8h.html</filename>
    <anchor>structnormal__clipped__params</anchor>
  </compound>
  <compound kind="struct">
    <name>normal_params</name>
    <filename>param__generator__normal_8h.html</filename>
    <anchor>structnormal__params</anchor>
  </compound>
  <compound kind="struct">
    <name>one_to_one</name>
    <filename>connection__generator__one__to__one_8h.html</filename>
    <anchor>structone__to__one</anchor>
  </compound>
  <compound kind="struct">
    <name>packet_firing_data_t</name>
    <filename>neuron__impl__external__devices_8h.html</filename>
    <anchor>structpacket__firing__data__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a4bc362bd05c9b3025446358e7df79cf4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>value_as_payload</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a1c15a9d27cf4ab85aae0d7cdbd76724c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>min_value</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>aaf0e80b11974d83d0b549c4959e9ba44</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>max_value</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a30e273060e625b08383af55e558345f3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>timesteps_between_sending</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a94013019ac141f16e20610a549dbb4a3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time_until_next_send</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>adfa239fbae3b207c2802724ad7a53d47</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>enum send_type</type>
      <name>type</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>af2e63c0a0d937a06c71a10b3e34b71a7</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>param_generator_constant</name>
    <filename>param__generator__constant_8h.html</filename>
    <anchor>structparam__generator__constant</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_exponential</name>
    <filename>param__generator__exponential_8h.html</filename>
    <anchor>structparam__generator__exponential</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_exponential_params</name>
    <filename>param__generator__exponential_8h.html</filename>
    <anchor>structparam__generator__exponential__params</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_info</name>
    <filename>param__generator_8c.html</filename>
    <anchor>structparam__generator__info</anchor>
    <member kind="variable">
      <type>generator_hash_t</type>
      <name>hash</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>ae88e70178562fa7a877beac81d249d8a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>initialize_func *</type>
      <name>initialize</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>abdee600112c11cf006a45596433f7293</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>generate_param_func *</type>
      <name>generate</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>ad9c1ec831eb4ff50829162738b662847</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>free_func *</type>
      <name>free</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a10a8a08f2a3dd4c64e428987d2c55ab3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>param_generator_kernel</name>
    <filename>param__generator__kernel_8h.html</filename>
    <anchor>structparam__generator__kernel</anchor>
    <member kind="variable">
      <type>uint16_t</type>
      <name>preWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a50ae2f03b893937f8d0529481c2a60a8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>preHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a561a1c087a1589446a958808ebe983d4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>postWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a2dba4c6db21eb4714b16bcf377cc4fb4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>postHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a012f441a8354f4adb8067835966ea0c5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPreWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a2cadcbfd06b082c35c8f177b42c9c471</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPreHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>ad6042855868420916ec7c5bbb232e26f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPostWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>ae4797b99153df747828fb6cc02dae9b0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>startPostHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a3d3d004bc42595ff42bdb210bada594b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPreWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a1e8efd89a833ec63e2f23a73fbd7c5cf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPreHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>af28477f63c374f6522fa6a522e9e259c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPostWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a3865ce7c696b02b3edd50b56f347a825</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>stepPostHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a0e44200f8fb728fd79e477862340e55c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>kernelWidth</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a0d01aa03a26db10e49797f513dbbd9ef</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>kernelHeight</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>ae62905eebe003437d597af683f38bcc5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>post_slice_start</name>
      <anchorfile>param__generator__kernel_8h.html</anchorfile>
      <anchor>a4e6a2883a116a6d2af96d2b0c444995d</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>param_generator_normal</name>
    <filename>param__generator__normal_8h.html</filename>
    <anchor>structparam__generator__normal</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_normal_clipped</name>
    <filename>param__generator__normal__clipped_8h.html</filename>
    <anchor>structparam__generator__normal__clipped</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_normal_clipped_boundary</name>
    <filename>param__generator__normal__clipped__to__boundary_8h.html</filename>
    <anchor>structparam__generator__normal__clipped__boundary</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator</name>
    <filename>param__generator_8c.html</filename>
    <anchor>structparam__generator</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_uniform</name>
    <filename>param__generator__uniform_8h.html</filename>
    <anchor>structparam__generator__uniform</anchor>
  </compound>
  <compound kind="struct">
    <name>plastic_synapse_t</name>
    <filename>synapse__structure__weight__state__accumulator__window__impl_8h.html</filename>
    <anchor>structplastic__synapse__t</anchor>
    <member kind="variable">
      <type>weight_t</type>
      <name>weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>aec514f5ba4eda9e82e4f7ea72f57440d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int16_t</type>
      <name>accumulator</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a168ee5175d6b41e154f2c502073a0773</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int8_t</type>
      <name>accumulator</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a81dfa0fab9f4f135705aa5425b7df228</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint8_t</type>
      <name>state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a3fb84deaa3f0d348fc69ece32370cb2d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>unsigned int</type>
      <name>weight</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a7ac24c0ef36c15e590f631882a976405</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int</type>
      <name>accumulator</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>ad8b18e92c0b384381b143522c94c20bd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>unsigned int</type>
      <name>state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a8475ff0e503b4b1cc73d9c4291ef949d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>unsigned int</type>
      <name>window_length</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a005d2c70b80ed435ef9e3a1910972c82</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>plasticity_trace_region_data_t</name>
    <filename>timing__vogels__2011__impl_8h.html</filename>
    <anchor>structplasticity__trace__region__data__t</anchor>
    <member kind="variable">
      <type>int32_t</type>
      <name>accumulator_depression_plus_one</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a80bb27d51d160545e2d8fb426957f729</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>accumulator_potentiation_minus_one</name>
      <anchorfile>timing__vogels__2011__impl_8h.html</anchorfile>
      <anchor>a3cf41b130b86f7b9b5507c5e86ed2085</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>plasticity_weight_region_data_t</name>
    <filename>weight__multiplicative__impl_8h.html</filename>
    <anchor>structplasticity__weight__region__data__t</anchor>
    <member kind="variable">
      <type>int32_t</type>
      <name>min_weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a36f5f4963507aee1e1b89073beacb446</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>max_weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a9817170000d877d61456458dd05bc244</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a2_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a45fa5e6af8e2d8e3b7cc9d1187ea02c0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a2_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a1bceb56b2b990e4b5f9c53e73b2e7570</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a3_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a441609a44c135858dab361177ca9aa78</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a3_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a2ae152e07fa65df3ce3b142030adae6e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>poisson_extension_provenance</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structpoisson__extension__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>times_tdma_fell_behind</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1a4790914bd12e136b3b9f1de01a920a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>pop_table_config_t</name>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <anchor>structpop__table__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>post_event_history_t</name>
    <filename>post__events_8h.html</filename>
    <anchor>structpost__event__history__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count_minus_one</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a55510f69f9fd514e9c470fedb286a3e6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>times</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>af548dcd857ce571d7546df85a9353332</anchor>
      <arglist>[MAX_POST_SYNAPTIC_EVENTS]</arglist>
    </member>
    <member kind="variable">
      <type>post_trace_t</type>
      <name>traces</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>af97afea1a11707f22b03a459cae5d8b0</anchor>
      <arglist>[MAX_POST_SYNAPTIC_EVENTS]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>post_event_window_t</name>
    <filename>post__events_8h.html</filename>
    <anchor>structpost__event__window__t</anchor>
    <member kind="variable">
      <type>post_trace_t</type>
      <name>prev_trace</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a92eee3c2aff3ee0df3e06e34c7551117</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>aaafc21255dcf5512f9c1751719ba0b0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const post_trace_t *</type>
      <name>next_trace</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>ac8965ef8cab18d79f9f329602b05c26c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const uint32_t *</type>
      <name>next_time</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a9e1d7d36e09369711dca6fd87e8bf756</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>num_events</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>a482244387a63c58164abb271f16d90f3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time_valid</name>
      <anchorfile>post__events_8h.html</anchorfile>
      <anchor>ae21ceec3f1432649f568ae24e265185a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>post_to_pre_entry</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structpost__to__pre__entry</anchor>
  </compound>
  <compound kind="struct">
    <name>post_trace_t</name>
    <filename>timing__recurrent__pre__stochastic__impl_8h.html</filename>
    <anchor>structpost__trace__t</anchor>
  </compound>
  <compound kind="struct">
    <name>pre_event_history_t</name>
    <filename>synapse__dynamics__stdp__mad__impl_8c.html</filename>
    <anchor>structpre__event__history__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ace155e5e7a0d0b2c67c5e1a802c7608e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>pre_trace_t</type>
      <name>prev_trace</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a36f385470c61c31c5afac9c875674ff2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>pre_info_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structpre__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>pre_pop_info_table_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structpre__pop__info__table__t</anchor>
  </compound>
  <compound kind="struct">
    <name>pre_stochastic_config_t</name>
    <filename>timing__recurrent__pre__stochastic__impl_8c.html</filename>
    <anchor>structpre__stochastic__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>pre_trace_t</name>
    <filename>timing__recurrent__pre__stochastic__impl_8h.html</filename>
    <anchor>structpre__trace__t</anchor>
  </compound>
  <compound kind="struct">
    <name>recording_info_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structrecording__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>recording_values_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structrecording__values__t</anchor>
  </compound>
  <compound kind="struct">
    <name>rewiring_data_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structrewiring__data__t</anchor>
  </compound>
  <compound kind="struct">
    <name>rng</name>
    <filename>rng_8c.html</filename>
    <anchor>structrng</anchor>
  </compound>
  <compound kind="struct">
    <name>robot_motor_control_provenance</name>
    <filename>robot__motor__control_8c.html</filename>
    <anchor>structrobot__motor__control__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_input_buffer_overflows</name>
      <anchorfile>robot__motor__control_8c.html</anchorfile>
      <anchor>adaf680d39b72069f2abf3665d1e2138e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>row_fixed_t</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>structrow__fixed__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_fixed_size</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a50513b263bb1530181ec2249d40876aa</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_plastic_size</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aca679fca0fd0e98eb46d35a6e4ac339e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>fixed_plastic_data</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a62f87e5f8fd8c442ad57b70a1ee4b82d</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>row_plastic_t</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>structrow__plastic__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>plastic_plastic_size</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ab11ee202b7e36d36c7f6d51d6d18601e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>plastic_plastic_data</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a1eaec93baa36091cabe09e821b0e60a1</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>single_synaptic_row_t</name>
    <filename>direct__synapses_8c.html</filename>
    <anchor>structsingle__synaptic__row__t</anchor>
    <member kind="variable">
      <type>const uint32_t</type>
      <name>n_plastic</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a1b6fa98c7e08a0ef08fc5211be5ae829</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const uint32_t</type>
      <name>n_fixed</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a98e324626937fff9c6246c5fe23aa1a6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const uint32_t</type>
      <name>n_plastic_controls</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a3f71526e9df46b5cef9c3b485e15dd6c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_datum</name>
      <anchorfile>direct__synapses_8c.html</anchorfile>
      <anchor>a009a320a0562e47977f8f408c72e2859</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>source_info</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structsource__info</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_rates</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a62435794d07ae2d9589f23e7e318cf65</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>index</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a5d2b3e7270a501214853d5105f536faf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>spike_source_t</type>
      <name>poissons</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a489d13f6c68c512fda05e069a5383947</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>spike_source_t</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structspike__source__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>start_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a69d2ea442b9a3cd15724c7bf80d02f6a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>end_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a64607ac2fa64b0549d111b2b84cbb51e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>next_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa9931cbd5389b3c46b8c0a4de4d0aa77</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>is_fast_source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a891758695b252c5b4c43c98b8f3232d4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UFRACT</type>
      <name>exp_minus_lambda</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ad312952bbda1eb46855036a9ec72c738</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>sqrt_lambda</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a0f76e635e260b47d8e260740166324cd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mean_isi_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aab41a5a325aec875f6f6b5dc7253aa74</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time_to_spike_ticks</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a939c2987f014e9004e52db891d73a845</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>static_row_t</name>
    <filename>matrix__generator__static_8h.html</filename>
    <anchor>structstatic__row__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>plastic_plastic_size</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a517f946e7eb90f3e7adaad0aad281bba</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_fixed_size</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a42b25ad87ad6746a462ba9ba0db13be4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_plastic_size</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a478e204c92e1d085b8f6649bfac26abd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_fixed_data</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a70c4dcee5d9f79d3d8d93e71816b28f1</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>stdp_params</name>
    <filename>synapse__dynamics__stdp__mad__impl_8c.html</filename>
    <anchor>structstdp__params</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>backprop_delay</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a06c22d077ef52c561ae4d0ea9f64d7ff</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_param_t</name>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <anchor>structsynapse__param__t</anchor>
    <member kind="variable">
      <type>alpha_params_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a54c6d9b5e32ee070e6f3fc350bd3dc27</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>alpha_params_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a603098082c6122c49eaaee5220b91c36</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>delta_params_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a8f91b2c0aa9a88c2b44e086fc94e6e24</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>delta_params_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a39087de65c4c33969bbfa69fee75697d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a54c6d9b5e32ee070e6f3fc350bd3dc27</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>exc2</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac7188feb692fb36784afed3e29e1db7b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a603098082c6122c49eaaee5220b91c36</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>multiplicator</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ae5a2dbf2b4410eb054592c7dd981354a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exc2_old</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a8d690bc6f7611e73dc3f2841d7bfbc91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>scaling_factor</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>af29469cba3047bb7b6f9b64eb0daf0bf</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_row_fixed_part_t</name>
    <filename>synapse__row_8h.html</filename>
    <anchor>structsynapse__row__fixed__part__t</anchor>
    <member kind="variable">
      <type>size_t</type>
      <name>num_fixed</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>abcd7dcde31cc1360f88b1144ced8bb95</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>size_t</type>
      <name>num_plastic</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ab3e10a5433e7d3f0d06c9441b8faa8b1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>data</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a18bc3789fb8e08ce5623f8a2dde8fce8</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_row_plastic_data_t</name>
    <filename>synapse__dynamics__stdp__mad__impl_8c.html</filename>
    <anchor>structsynapse__row__plastic__data__t</anchor>
    <member kind="variable">
      <type>pre_event_history_t</type>
      <name>history</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>af0d2f303f8c9aa1663c98c13b53b7ed5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>plastic_synapse_t</type>
      <name>synapses</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a8ca99776251ff7551be58b738b7d5380</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_row_plastic_part_t</name>
    <filename>synapse__row_8h.html</filename>
    <anchor>structsynapse__row__plastic__part__t</anchor>
    <member kind="variable">
      <type>size_t</type>
      <name>size</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a5c73ad1ce7793ac1613afb98920fcf17</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>data</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>afc071194a0530bc45311760c805ef761</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>threshold_type_t</name>
    <filename>threshold__type__static_8h.html</filename>
    <anchor>structthreshold__type__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>du_th_inv</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>acaf821c33da7ceffd34956d24bef0d3a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>tau_th_inv</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>ae06bd5cdb86afcc206e80fc52f08944f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_thresh</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>ab45ec840ac2e212feee7e2b5782a8ed0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>neg_machine_time_step_ms_div_10</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>ad4d04f4117f32c07cd86ee51cdc9eb74</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>threshold_value</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a8d25a3b92dbeffe773c096f0289aeb44</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>timed_out_spikes</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structtimed__out__spikes</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a33ac2a85b7e7fa98bf0905b205694eb3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_buffers</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a01eac79ac7d1bc6bc5ba8bbe4fcdfa6c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>out_spikes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a5e1cb4999f85fa84e66c575788e3bef6</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>uniform_params</name>
    <filename>param__generator__uniform_8h.html</filename>
    <anchor>structuniform__params</anchor>
  </compound>
  <compound kind="struct">
    <name>update_state_t</name>
    <filename>synapse__structure__weight__state__accumulator__window__impl_8h.html</filename>
    <anchor>structupdate__state__t</anchor>
    <member kind="variable">
      <type>weight_state_t</type>
      <name>weight_state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a45deb71a19d3315499d0e7f8a1b903bd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>accumulator</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>ac3e795c15300742ba52853e1bb5b8006</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>state</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a84871d6882d55c00c9723a167198811c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>window_length</name>
      <anchorfile>synapse__structure__weight__state__accumulator__window__impl_8h.html</anchorfile>
      <anchor>a2d508676e6b481d3498c2920efee4d3a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>vogels_2011_config_t</name>
    <filename>timing__vogels__2011__impl_8c.html</filename>
    <anchor>structvogels__2011__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>weight_state_t</name>
    <filename>weight__multiplicative__impl_8h.html</filename>
    <anchor>structweight__state__t</anchor>
    <member kind="variable">
      <type>int32_t</type>
      <name>initial_weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a00e03d7e3edfe78ae928b1e3ce668251</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a2_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>ab6618f4c15ae163d34944b87abb1616e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a2_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a7702d7b6ccf0c9b5bf5fd5d56b474069</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const plasticity_weight_region_data_t *</type>
      <name>weight_region</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a037ff5bb63dd02afd72abd232bfd09ca</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a3_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>aff2684eb438bfed48cf8e73a5c420570</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>a3_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a362de6063e9a54fa204530f8e2c2bdc2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a6558f10355845b02cd9316f74d7e92be</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>weight_multiply_right_shift</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a7239d63b32b5b4e7d8c2a6b6dd270671</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="page">
    <name>index</name>
    <title>sPyNNaker: A PyNN Implementation for SpiNNaker</title>
    <filename>index.html</filename>
    <docanchor file="index.html" title="Neuron Simulation Implementation">neuron</docanchor>
    <docanchor file="index.html" title="Support Binaries">support</docanchor>
  </compound>
</tagfile>
