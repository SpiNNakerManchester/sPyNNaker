<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<tagfile doxygen_version="1.9.8">
  <compound kind="file">
    <name>in_spikes.h</name>
    <path>src/common/</path>
    <filename>in__spikes_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="yes" import="no" module="no" objc="no">neuron-typedefs.h</includes>
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
    <path>src/common/</path>
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
      <name>SQRTU</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a7d7e418d74fe9c51ff761e95c53b36ce</anchor>
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
      <name>EXPU</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a434280e3efa8104178a0cc10cb56f0c4</anchor>
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
    <member kind="function" static="yes">
      <type>static REAL</type>
      <name>kdivk</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a93c5e8722291b50b8a17e64cf8d5edb9</anchor>
      <arglist>(REAL a, REAL b)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static UREAL</type>
      <name>ukdivuk</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>aad39b7916d4863f936206b699997aff1</anchor>
      <arglist>(UREAL a, UREAL b)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>udivk</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a8fa3dde0c1762bfdb7e5f0c72dd5ac44</anchor>
      <arglist>(int32_t a, REAL b)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static REAL</type>
      <name>kdivui</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ab6e6f665bddb5253982e560b4b2969c5</anchor>
      <arglist>(REAL a, uint32_t b)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static UREAL</type>
      <name>pow_of_2</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>a03cafd4286b9fe615a385e4dab2d5661</anchor>
      <arglist>(REAL p)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const uint32_t</type>
      <name>fract_powers_2</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>abb38685f45ce9c8eb5d4e97abd17ec84</anchor>
      <arglist>[]</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const uint32_t</type>
      <name>fract_powers_half</name>
      <anchorfile>maths-util_8h.html</anchorfile>
      <anchor>ae38cf018c6a9bd98947ca008c9e519ff</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>munich_protocol.h</name>
    <path>src/common/</path>
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
    <path>src/common/</path>
    <filename>neuron-typedefs_8h.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="yes" import="no" module="no" objc="no">maths-util.h</includes>
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
    <path>src/delay_extension/</path>
    <filename>delay__extension_8c.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="yes" import="no" module="no" objc="no">delay_extension.h</includes>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" import="no" module="no" objc="no">common/in_spikes.h</includes>
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
      <name>user_callback</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>ab12cbb036b0ea4fb48a72d1d910cefa7</anchor>
      <arglist>(uint unused0, uint unused1)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>background_callback</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a49c7afe548d59aec1ea053bdde97724d</anchor>
      <arglist>(uint local_time, uint timer_count)</arglist>
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
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_colour_bits</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a94d9d348a8da10a4851d8c5cc344ab27</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>colour_mask</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a4aa662177b306e9085f7ef20b3a6a2c1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>colour</name>
      <anchorfile>delay__extension_8c.html</anchorfile>
      <anchor>a5bdac4fec3cf570ebe861aea93346316</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>delay_extension.h</name>
    <path>src/delay_extension/</path>
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
      <name>TDMA_REGION</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a6e4d67a0bd74db4da98539f8d2e5ab32a3ec559988321d901a9631875c4782ba6</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>additional_input.h</name>
    <path>src/neuron/additional_inputs/</path>
    <filename>additional__input_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_initialise</name>
      <anchorfile>additional__input_8h.html</anchorfile>
      <anchor>aadbad417439bccd417fa263908cf5f23</anchor>
      <arglist>(additional_input_t *state, additional_input_params_t *params, uint32_t n_steps_per_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_save_state</name>
      <anchorfile>additional__input_8h.html</anchorfile>
      <anchor>abb4f4a48858a047e98636c6c4c91c97b</anchor>
      <arglist>(additional_input_t *state, additional_input_params_t *params)</arglist>
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
    <path>src/neuron/additional_inputs/</path>
    <filename>additional__input__ca2__adaptive__impl_8h.html</filename>
    <includes id="additional__input_8h" name="additional_input.h" local="yes" import="no" module="no" objc="no">additional_input.h</includes>
    <class kind="struct">additional_input_params_t</class>
    <class kind="struct">additional_input_t</class>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>additional_input_get_input_value_as_current</name>
      <anchorfile>additional__input__ca2__adaptive__impl_8h.html</anchorfile>
      <anchor>a9e4d2b22f1906900e72db9131cf3822b</anchor>
      <arglist>(additional_input_t *additional_input, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_has_spiked</name>
      <anchorfile>additional__input__ca2__adaptive__impl_8h.html</anchorfile>
      <anchor>ab82803acdc9d245f4d1275928dea72e8</anchor>
      <arglist>(additional_input_t *additional_input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>additional_input_none_impl.h</name>
    <path>src/neuron/additional_inputs/</path>
    <filename>additional__input__none__impl_8h.html</filename>
    <includes id="additional__input_8h" name="additional_input.h" local="yes" import="no" module="no" objc="no">additional_input.h</includes>
    <class kind="struct">additional_input_params_t</class>
    <class kind="struct">additional_input_t</class>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>additional_input_get_input_value_as_current</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a9e4d2b22f1906900e72db9131cf3822b</anchor>
      <arglist>(additional_input_t *additional_input, state_t membrane_voltage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>additional_input_has_spiked</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>ab82803acdc9d245f4d1275928dea72e8</anchor>
      <arglist>(additional_input_t *additional_input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>c_main.c</name>
    <path>src/neuron/</path>
    <filename>c__main_8c.html</filename>
    <includes id="regions_8h" name="regions.h" local="yes" import="no" module="no" objc="no">regions.h</includes>
    <includes id="neuron_2profile__tags_8h" name="profile_tags.h" local="yes" import="no" module="no" objc="no">profile_tags.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" import="no" module="no" objc="no">spike_processing.h</includes>
    <class kind="struct">combined_provenance</class>
    <member kind="enumeration">
      <type></type>
      <name>callback_priorities</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>c_main_store_provenance_data</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a1dc4d17392d4c0a6dac7ab12267da487</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>resume_callback</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a8967e8eb09363007076f840186a20995</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>process_ring_buffers</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a7877934d7f174e52d11945b3a893b7d7</anchor>
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
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>abc8ec4992e18193766cc267a4968f1d7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>const struct common_regions</type>
      <name>COMMON_REGIONS</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ac4b08337fb78e995265b4091aeeb3543</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct common_priorities</type>
      <name>COMMON_PRIORITIES</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>ab8a24477bf90774dbe741f1aa007d394</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct neuron_regions</type>
      <name>NEURON_REGIONS</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a36f1dda69af112b3e9f1fcc7d708aa53</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct synapse_regions</type>
      <name>SYNAPSE_REGIONS</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>aabee4d4d7d12350e84247cd6af69d388</anchor>
      <arglist></arglist>
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
      <type>static uint32_t</type>
      <name>recording_flags</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a9a97f21dc7fccaac8071bcd29894bccb</anchor>
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
    <member kind="variable" static="yes">
      <type>static weight_t *</type>
      <name>ring_buffers</name>
      <anchorfile>c__main_8c.html</anchorfile>
      <anchor>a9d013c2e9d5eddd8472bd57e9b21ff99</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>c_main_neurons.c</name>
    <path>src/neuron/</path>
    <filename>c__main__neurons_8c.html</filename>
    <includes id="neuron_2profile__tags_8h" name="profile_tags.h" local="yes" import="no" module="no" objc="no">profile_tags.h</includes>
    <class kind="struct">sdram_config</class>
    <class kind="struct">neurons_provenance</class>
    <member kind="define">
      <type>#define</type>
      <name>N_SYNAPTIC_BUFFERS</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a6f2bb64a1d2e6a72f6f5a7fd2133bd37</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>callback_priorities</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>regions</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a4c4786354df7358bf12c3c65069dd8b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>store_provenance_data</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a6a6f18428eca2d03be2d82834e642876</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>resume_callback</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a8967e8eb09363007076f840186a20995</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>sum</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a5ffff1e601916bbafe975ffd014d063b</anchor>
      <arglist>(weight_t *syns)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>timer_callback</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a217aea663c8dd444052831cbde49bd62</anchor>
      <arglist>(uint timer_count, uint unused)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>abc8ec4992e18193766cc267a4968f1d7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>const struct common_regions</type>
      <name>COMMON_REGIONS</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>ac4b08337fb78e995265b4091aeeb3543</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct common_priorities</type>
      <name>COMMON_PRIORITIES</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>ab8a24477bf90774dbe741f1aa007d394</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct neuron_regions</type>
      <name>NEURON_REGIONS</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a36f1dda69af112b3e9f1fcc7d708aa53</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_period</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>ac0c27301e134af3ce80814a553601074</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>recording_flags</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a9a97f21dc7fccaac8071bcd29894bccb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static struct sdram_config</type>
      <name>sdram_inputs</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a9f249060c5bd10f51d18ac31811e335a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static weight_t *</type>
      <name>synaptic_contributions</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a7ec04742355ddb6ef2646f8fe73537f3</anchor>
      <arglist>[N_SYNAPTIC_BUFFERS]</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_overruns</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>ab906ad7ebd877998e633aab4cea0f532</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static union @7</type>
      <name>all_synaptic_contributions</name>
      <anchorfile>c__main__neurons_8c.html</anchorfile>
      <anchor>a929e7d4597a748597e4570ea31dc44ac</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>c_main_synapses.c</name>
    <path>src/neuron/</path>
    <filename>c__main__synapses_8c.html</filename>
    <includes id="spike__processing__fast_8h" name="spike_processing_fast.h" local="yes" import="no" module="no" objc="no">spike_processing_fast.h</includes>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" import="no" module="no" objc="no">structural_plasticity/synaptogenesis_dynamics.h</includes>
    <class kind="struct">provenance_data</class>
    <member kind="enumeration">
      <type></type>
      <name>callback_priorities</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a65b19dabf5283c1ea37df964ca25e964</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <type></type>
      <name>regions</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a4c4786354df7358bf12c3c65069dd8b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>store_provenance_data</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a6a6f18428eca2d03be2d82834e642876</anchor>
      <arglist>(address_t provenance_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>resume_callback</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a8967e8eb09363007076f840186a20995</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>timer_callback</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>ac9914f4341d050b71b5e1516eb19a184</anchor>
      <arglist>(uint unused0, uint unused1)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>abc8ec4992e18193766cc267a4968f1d7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>const struct common_regions</type>
      <name>COMMON_REGIONS</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>ac4b08337fb78e995265b4091aeeb3543</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct common_priorities</type>
      <name>COMMON_PRIORITIES</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>ab8a24477bf90774dbe741f1aa007d394</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const struct synapse_regions</type>
      <name>SYNAPSE_REGIONS</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>aabee4d4d7d12350e84247cd6af69d388</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>ae73654f333e4363463ad8c594eca1905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>timer_period</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>ac0c27301e134af3ce80814a553601074</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>simulation_ticks</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a2178bb4764f423b1534a9631b0cc6e5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>infinite_run</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a9ee6c18f2c55e2b60ea4194d4722f735</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>recording_flags</name>
      <anchorfile>c__main__synapses_8c.html</anchorfile>
      <anchor>a9a97f21dc7fccaac8071bcd29894bccb</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>current_source.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <class kind="struct">cs_id_index_t</class>
    <class kind="struct">neuron_current_source_t</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>current_source_initialise</name>
      <anchorfile>current__source_8h.html</anchorfile>
      <anchor>a1727a6ad7e793067911f98682712f04f</anchor>
      <arglist>(address_t cs_address, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>current_source_load_parameters</name>
      <anchorfile>current__source_8h.html</anchorfile>
      <anchor>ab3839d2a4faec82656c552e338002957</anchor>
      <arglist>(address_t cs_address)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static REAL</type>
      <name>current_source_get_offset</name>
      <anchorfile>current__source_8h.html</anchorfile>
      <anchor>aa5c5460b1828e797dd328c38e48fda6f</anchor>
      <arglist>(uint32_t time, uint32_t neuron_index)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>current_source_ac.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__ac_8h.html</filename>
    <class kind="struct">ac_source_t</class>
  </compound>
  <compound kind="file">
    <name>current_source_ac_only_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__ac__only__impl_8h.html</filename>
    <includes id="current__source__ac_8h" name="current_source_ac.h" local="yes" import="no" module="no" objc="no">current_source_ac.h</includes>
  </compound>
  <compound kind="file">
    <name>current_source_dc.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__dc_8h.html</filename>
    <class kind="struct">dc_source_t</class>
  </compound>
  <compound kind="file">
    <name>current_source_dc_only_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__dc__only__impl_8h.html</filename>
    <includes id="current__source__dc_8h" name="current_source_dc.h" local="yes" import="no" module="no" objc="no">current_source_dc.h</includes>
  </compound>
  <compound kind="file">
    <name>current_source_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__impl_8h.html</filename>
    <includes id="current__source__dc_8h" name="current_source_dc.h" local="yes" import="no" module="no" objc="no">current_source_dc.h</includes>
    <includes id="current__source__ac_8h" name="current_source_ac.h" local="yes" import="no" module="no" objc="no">current_source_ac.h</includes>
    <includes id="current__source__step_8h" name="current_source_step.h" local="yes" import="no" module="no" objc="no">current_source_step.h</includes>
    <includes id="current__source__noisy_8h" name="current_source_noisy.h" local="yes" import="no" module="no" objc="no">current_source_noisy.h</includes>
  </compound>
  <compound kind="file">
    <name>current_source_noisy.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__noisy_8h.html</filename>
    <class kind="struct">noisy_current_source_t</class>
  </compound>
  <compound kind="file">
    <name>current_source_noisy_only_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__noisy__only__impl_8h.html</filename>
    <includes id="current__source__noisy_8h" name="current_source_noisy.h" local="yes" import="no" module="no" objc="no">current_source_noisy.h</includes>
  </compound>
  <compound kind="file">
    <name>current_source_step.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__step_8h.html</filename>
    <class kind="struct">step_current_source_times_t</class>
    <class kind="struct">step_current_source_amps_t</class>
  </compound>
  <compound kind="file">
    <name>current_source_step_only_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__step__only__impl_8h.html</filename>
    <includes id="current__source__step_8h" name="current_source_step.h" local="yes" import="no" module="no" objc="no">current_source_step.h</includes>
  </compound>
  <compound kind="file">
    <name>current_source_stepnoisy_impl.h</name>
    <path>src/neuron/current_sources/</path>
    <filename>current__source__stepnoisy__impl_8h.html</filename>
    <includes id="current__source__step_8h" name="current_source_step.h" local="yes" import="no" module="no" objc="no">current_source_step.h</includes>
    <includes id="current__source__noisy_8h" name="current_source_noisy.h" local="yes" import="no" module="no" objc="no">current_source_noisy.h</includes>
  </compound>
  <compound kind="file">
    <name>decay.h</name>
    <path>src/neuron/</path>
    <filename>decay_8h.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
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
    <name>neuron_impl.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
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
      <anchor>a6096589e60619a6e460d1f3b2438b72d</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons, address_t save_initial_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a5c11520af8e2915ec00d5dc1edcd8b36</anchor>
      <arglist>(uint32_t timer_count, uint32_t time, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_store_neuron_parameters</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>af2c8c3ce110bf3e9b4d0dc27f22b4860</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_print_inputs</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>acd93dc53f9853bbfdc0f8f410c475431</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_print_synapse_parameters</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>a1095c8e988d10fd07d007592b99f8594</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>neuron_impl_get_synapse_type_char</name>
      <anchorfile>neuron__impl_8h.html</anchorfile>
      <anchor>aa3a8b2d8849b4fb09ba312151d0e9204</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_external_devices.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl__external__devices_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" import="no" module="no" objc="no">neuron_impl.h</includes>
    <includes id="neuron__model__lif__impl_8h" name="neuron_model_lif_impl.h" local="no" import="no" module="no" objc="no">neuron/models/neuron_model_lif_impl.h</includes>
    <includes id="synapse__types__exponential__impl_8h" name="synapse_types_exponential_impl.h" local="no" import="no" module="no" objc="no">neuron/synapse_types/synapse_types_exponential_impl.h</includes>
    <includes id="input__type__current_8h" name="input_type_current.h" local="no" import="no" module="no" objc="no">neuron/input_types/input_type_current.h</includes>
    <includes id="current__source__impl_8h" name="current_source_impl.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source_impl.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" import="no" module="no" objc="no">neuron/neuron_recording.h</includes>
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
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a5c11520af8e2915ec00d5dc1edcd8b36</anchor>
      <arglist>(uint32_t timer_count, uint32_t time, uint32_t n_neurons)</arglist>
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
      <anchor>a4be4472805fe2eec8f026aa658005a36</anchor>
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
      <type>static packet_firing_data_t *</type>
      <name>packet_firing_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>a8870077736fbcaca0d2aba2bb33f1040</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static synapse_types_t *</type>
      <name>synapse_types_array</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>aed1e3706b58fb9163d3009b05e9b41ef</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint</type>
      <name>n_steps_per_timestep</name>
      <anchorfile>neuron__impl__external__devices_8h.html</anchorfile>
      <anchor>adc2145aaa2f8435401d2c077d42c7b91</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_standard.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl__standard_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" import="no" module="no" objc="no">neuron_impl.h</includes>
    <includes id="neuron__model_8h" name="neuron_model.h" local="no" import="no" module="no" objc="no">neuron/models/neuron_model.h</includes>
    <includes id="input__type_8h" name="input_type.h" local="no" import="no" module="no" objc="no">neuron/input_types/input_type.h</includes>
    <includes id="additional__input_8h" name="additional_input.h" local="no" import="no" module="no" objc="no">neuron/additional_inputs/additional_input.h</includes>
    <includes id="threshold__type_8h" name="threshold_type.h" local="no" import="no" module="no" objc="no">neuron/threshold_types/threshold_type.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="no" import="no" module="no" objc="no">neuron/synapse_types/synapse_types.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" import="no" module="no" objc="no">neuron/neuron_recording.h</includes>
    <member kind="enumeration">
      <type></type>
      <name>word_recording_indices</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a68f96be069d7309d70ec3343afad2e03</anchor>
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
      <anchor>a6096589e60619a6e460d1f3b2438b72d</anchor>
      <arglist>(address_t address, uint32_t next, uint32_t n_neurons, address_t save_initial_state)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_impl_do_timestep_update</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>a5c11520af8e2915ec00d5dc1edcd8b36</anchor>
      <arglist>(uint32_t timer_count, uint32_t time, uint32_t n_neurons)</arglist>
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
      <anchor>a4be4472805fe2eec8f026aa658005a36</anchor>
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
      <type>static synapse_types_t *</type>
      <name>synapse_types_array</name>
      <anchorfile>neuron__impl__standard_8h.html</anchorfile>
      <anchor>aed1e3706b58fb9163d3009b05e9b41ef</anchor>
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
    <name>neuron_impl_stoc_exp.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl__stoc__exp_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="no" import="no" module="no" objc="no">neuron/implementations/neuron_impl.h</includes>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" import="no" module="no" objc="no">neuron/neuron_recording.h</includes>
    <includes id="current__source__impl_8h" name="current_source_impl.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source_impl.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source.h</includes>
    <includes id="stoc__exp__common_8h" name="stoc_exp_common.h" local="yes" import="no" module="no" objc="no">stoc_exp_common.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_impl_t</class>
    <member kind="variable" static="yes">
      <type>static neuron_impl_t *</type>
      <name>neuron_array</name>
      <anchorfile>neuron__impl__stoc__exp_8h.html</anchorfile>
      <anchor>a209605cbeeebb5cd81cbd1e26a2fe1f3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_stoc_exp_stable.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl__stoc__exp__stable_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="no" import="no" module="no" objc="no">neuron/implementations/neuron_impl.h</includes>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" import="no" module="no" objc="no">neuron/neuron_recording.h</includes>
    <includes id="current__source__impl_8h" name="current_source_impl.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source_impl.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source.h</includes>
    <includes id="stoc__exp__common_8h" name="stoc_exp_common.h" local="yes" import="no" module="no" objc="no">stoc_exp_common.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_impl_t</class>
    <member kind="variable" static="yes">
      <type>static neuron_impl_t *</type>
      <name>neuron_array</name>
      <anchorfile>neuron__impl__stoc__exp__stable_8h.html</anchorfile>
      <anchor>a209605cbeeebb5cd81cbd1e26a2fe1f3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_impl_stoc_sigma.h</name>
    <path>src/neuron/implementations/</path>
    <filename>neuron__impl__stoc__sigma_8h.html</filename>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="no" import="no" module="no" objc="no">neuron/implementations/neuron_impl.h</includes>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="no" import="no" module="no" objc="no">neuron/neuron_recording.h</includes>
    <includes id="current__source__impl_8h" name="current_source_impl.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source_impl.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="no" import="no" module="no" objc="no">neuron/current_sources/current_source.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_impl_t</class>
    <member kind="define">
      <type>#define</type>
      <name>PROB_HALF</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>ab49cae6f7784ccc3fa600a6aeb2631c4</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>MAX_POWER</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a6e5f254e637637d3a3256dfd7a1399c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static neuron_impl_t *</type>
      <name>neuron_array</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a209605cbeeebb5cd81cbd1e26a2fe1f3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>stoc_exp_common.h</name>
    <path>src/neuron/implementations/</path>
    <filename>stoc__exp__common_8h.html</filename>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_probability</name>
      <anchorfile>stoc__exp__common_8h.html</anchorfile>
      <anchor>a9f0abc6e7d8d0554710c01336d6e2b35</anchor>
      <arglist>(UREAL tau, REAL p)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const uint32_t</type>
      <name>MIN_TAU</name>
      <anchorfile>stoc__exp__common_8h.html</anchorfile>
      <anchor>a9100a4cc657cf64c13e2533439ce4ae5</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>input_type.h</name>
    <path>src/neuron/input_types/</path>
    <filename>input__type_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
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
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_initialise</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>a26f363df8042bd869bd06d36744bfbee</anchor>
      <arglist>(input_type_t *state, input_type_params_t *params, uint32_t n_steps_per_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>input_type_save_state</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>ae174cb0d7c7d94f22ee29379c80b73b8</anchor>
      <arglist>(input_type_t *state, input_type_params_t *params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type_8h.html</anchorfile>
      <anchor>aa9549958c52a82155106995e64f1a3f2</anchor>
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
    <path>src/neuron/input_types/</path>
    <filename>input__type__conductance_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" import="no" module="no" objc="no">input_type.h</includes>
    <class kind="struct">input_type_params_t</class>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__conductance_8h.html</anchorfile>
      <anchor>aa9549958c52a82155106995e64f1a3f2</anchor>
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
    <path>src/neuron/input_types/</path>
    <filename>input__type__current_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" import="no" module="no" objc="no">input_type.h</includes>
    <class kind="struct">input_type_params_t</class>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__current_8h.html</anchorfile>
      <anchor>aa9549958c52a82155106995e64f1a3f2</anchor>
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
  </compound>
  <compound kind="file">
    <name>input_type_delta.h</name>
    <path>src/neuron/input_types/</path>
    <filename>input__type__delta_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" import="no" module="no" objc="no">input_type.h</includes>
    <class kind="struct">input_type_params_t</class>
    <class kind="struct">input_type_t</class>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>input_type_get_input_value</name>
      <anchorfile>input__type__delta_8h.html</anchorfile>
      <anchor>aa9549958c52a82155106995e64f1a3f2</anchor>
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
  </compound>
  <compound kind="file">
    <name>input_type_none.h</name>
    <path>src/neuron/input_types/</path>
    <filename>input__type__none_8h.html</filename>
    <includes id="input__type_8h" name="input_type.h" local="yes" import="no" module="no" objc="no">input_type.h</includes>
    <class kind="struct">input_type_params_t</class>
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
      <anchor>aa9549958c52a82155106995e64f1a3f2</anchor>
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
    <name>local_only.c</name>
    <path>src/neuron/</path>
    <filename>local__only_8c.html</filename>
    <includes id="local__only_8h" name="local_only.h" local="yes" import="no" module="no" objc="no">local_only.h</includes>
    <class kind="struct">local_only_config</class>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>run_next_process_loop</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a8831701fff5eb90d0b555d7f31d43042</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>update_max_input_buffer</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>acee9489bdd8e17e846dcb3c74d2da3ed</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>mc_rcv_callback</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>ac2e3ea3a78c3647c61f22207ce5672ab</anchor>
      <arglist>(uint key, uint unused)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>mc_rcv_payload_callback</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a3949ac26c77264d95a9def6a6f5bcf4b</anchor>
      <arglist>(uint key, uint n_spikes)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>process_callback</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>ad8723ad85d322f095cad1bfdaaef4553</anchor>
      <arglist>(uint time, uint unused1)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>local_only_initialise</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>ab5b33e9b7701dae5e7428563d1a0ef3f</anchor>
      <arglist>(void *local_only_addr, void *local_only_params_addr, uint32_t n_rec_regions_used, uint16_t **ring_buffers_ptr)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>local_only_clear_input</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a3386391863364f7ac04343b0757a094f</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>local_only_store_provenance</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>aae2aae4e4f0eda250ae9e657f3ff76f6</anchor>
      <arglist>(struct local_only_provenance *prov)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static struct local_only_config</type>
      <name>config</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>af0b65a4ae84767d39f100caae218e388</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static circular_buffer</type>
      <name>input_buffer</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>ace70899ad78873f586a55a1cce68769c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t *</type>
      <name>ring_buffers</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a498672d434f86e3eafe7ba5dfe9723f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static volatile bool</type>
      <name>process_loop_running</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a00274a0a6ae804ced8644de7977d1991</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spikes_received</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>ab44a4c12259e8ce83d97b8aee67e06d3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>max_spikes_received</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a3e80365227aacafec58fa5b3568b7232</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_spikes_dropped</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a23c1f67726948c3a4106832e5143a269</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>max_input_buffer_size</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a570999fa4da7904a54b2ec7aa4163b49</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>local_time</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a8acaea2ca079944abe8a79230097072e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_delay_mask</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a2ef4427415ac67eb603a14ca1bb86f83</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>p_per_ts_region</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a940ad8bd79b6fbdb1fbce1341f2edf92</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static struct @8</type>
      <name>p_per_ts_struct</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>abee386e9b7c91432c51b469b547918cc</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>local_only.h</name>
    <path>src/neuron/</path>
    <filename>local__only_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <class kind="struct">local_only_provenance</class>
    <member kind="function">
      <type>bool</type>
      <name>local_only_initialise</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>aca5b2563f560424809ba0d64c22da063</anchor>
      <arglist>(void *local_only_addr, void *local_only_params_addr, uint32_t n_rec_regions_used, uint16_t **ring_buffers)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>local_only_clear_input</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>a3386391863364f7ac04343b0757a094f</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>local_only_store_provenance</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>aae2aae4e4f0eda250ae9e657f3ff76f6</anchor>
      <arglist>(struct local_only_provenance *prov)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model.h</name>
    <path>src/neuron/models/</path>
    <filename>neuron__model_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_initialise</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>ac5fc11951300c8a7321586ffb24b4107</anchor>
      <arglist>(neuron_t *state, neuron_params_t *params, uint32_t n_steps_per_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_save_state</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>add9582f47143d4a943af8bbd50082d4a</anchor>
      <arglist>(neuron_t *state, neuron_params_t *params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a6809c07eadc54841c5970164ca52dc3b</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, REAL current_offset, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a6d9e95529a2c510cc1010163f9ea89ee</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a36ed2fe89ac12da019a6bcee8b6672c9</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_print_state_variables</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>a34e146df45faa9cdf07da003881f0181</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_print_parameters</name>
      <anchorfile>neuron__model_8h.html</anchorfile>
      <anchor>ae984b1ab35b6ea027f5d622074c21212</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_if_trunc.h</name>
    <path>src/neuron/models/</path>
    <filename>neuron__model__if__trunc_8h.html</filename>
    <includes id="neuron__model_8h" name="neuron_model.h" local="yes" import="no" module="no" objc="no">neuron_model.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_t</class>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>lif_ceil_accum</name>
      <anchorfile>neuron__model__if__trunc_8h.html</anchorfile>
      <anchor>a9657bc9566431a1077df6f73dae27baf</anchor>
      <arglist>(REAL value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model__if__trunc_8h.html</anchorfile>
      <anchor>a6809c07eadc54841c5970164ca52dc3b</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, REAL current_offset, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model__if__trunc_8h.html</anchorfile>
      <anchor>a6d9e95529a2c510cc1010163f9ea89ee</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model__if__trunc_8h.html</anchorfile>
      <anchor>a36ed2fe89ac12da019a6bcee8b6672c9</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_izh_impl.h</name>
    <path>src/neuron/models/</path>
    <filename>neuron__model__izh__impl_8h.html</filename>
    <includes id="neuron__model_8h" name="neuron_model.h" local="yes" import="no" module="no" objc="no">neuron_model.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_t</class>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>rk2_kernel_midpoint</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>ae9b257f5e4059af3a5fa30730512f2b6</anchor>
      <arglist>(REAL h, neuron_t *neuron, REAL input_this_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>a6809c07eadc54841c5970164ca52dc3b</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, REAL current_offset, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>a6d9e95529a2c510cc1010163f9ea89ee</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>a36ed2fe89ac12da019a6bcee8b6672c9</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>SIMPLE_TQ_OFFSET</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>a2a9449a2c1269d81389014e6c2df9573</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static const REAL</type>
      <name>MAGIC_MULTIPLIER</name>
      <anchorfile>neuron__model__izh__impl_8h.html</anchorfile>
      <anchor>adf9a0e8d9c7ec24f407eee48d6064666</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_model_lif_impl.h</name>
    <path>src/neuron/models/</path>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <includes id="neuron__model_8h" name="neuron_model.h" local="yes" import="no" module="no" objc="no">neuron_model.h</includes>
    <class kind="struct">neuron_params_t</class>
    <class kind="struct">neuron_t</class>
    <member kind="function" static="yes">
      <type>static int32_t</type>
      <name>lif_ceil_accum</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a9657bc9566431a1077df6f73dae27baf</anchor>
      <arglist>(REAL value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>lif_neuron_closed_form</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>acdc543d115e02324c243ebbfdd303214</anchor>
      <arglist>(neuron_t *neuron, REAL V_prev, input_t input_this_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_state_update</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a6809c07eadc54841c5970164ca52dc3b</anchor>
      <arglist>(uint16_t num_excitatory_inputs, const input_t *exc_input, uint16_t num_inhibitory_inputs, const input_t *inh_input, input_t external_bias, REAL current_offset, neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>neuron_model_has_spiked</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a6d9e95529a2c510cc1010163f9ea89ee</anchor>
      <arglist>(neuron_t *restrict neuron)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static state_t</type>
      <name>neuron_model_get_membrane_voltage</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a36ed2fe89ac12da019a6bcee8b6672c9</anchor>
      <arglist>(const neuron_t *neuron)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron.c</name>
    <path>src/neuron/</path>
    <filename>neuron_8c.html</filename>
    <includes id="neuron_8h" name="neuron.h" local="yes" import="no" module="no" objc="no">neuron.h</includes>
    <includes id="neuron__recording_8h" name="neuron_recording.h" local="yes" import="no" module="no" objc="no">neuron_recording.h</includes>
    <includes id="neuron__impl_8h" name="neuron_impl.h" local="yes" import="no" module="no" objc="no">implementations/neuron_impl.h</includes>
    <includes id="current__source_8h" name="current_source.h" local="yes" import="no" module="no" objc="no">current_sources/current_source.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" import="no" module="no" objc="no">plasticity/synapse_dynamics.h</includes>
    <class kind="struct">neuron_core_parameters</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_load_neuron_parameters</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>aff90525477e8305d9754a5876cbdfb18</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_resume</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a82283d81b442ae011e830b3c3ab7882b</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_initialise</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a0e3fd26136f3e14f31f40f95bf4e9e54</anchor>
      <arglist>(void *core_params_address, void *neuron_params_address, void *current_sources_address, void *recording_address, void *initial_values_address, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_pause</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a09464219c59d7e79cbd4cf0acb9f96a1</anchor>
      <arglist>(void)</arglist>
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
      <name>neuron_transfer</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ab711f5128ef4a95c71bd123278bde9eb</anchor>
      <arglist>(weight_t *syns)</arglist>
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
      <anchor>a1352d326fa3e6bc9640b24bfd4cf2abd</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>neuron_keys</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>aeca2f0c73d9a6fa91f83208ea4e13ef4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bool</type>
      <name>use_key</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ab9132b5a04a7bdb8ac2e4293c1ec96bf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>latest_send_time</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a4e6ef8511daf9c94c849796f98b2a940</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>earliest_send_time</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>adb470808676e08ce78789a18a99da76e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>colour</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a5bdac4fec3cf570ebe861aea93346316</anchor>
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
      <name>n_neurons_peak</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a6b1b7d48e24674f12efcb5a84266f969</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_synapse_types</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>adedb27b3ece4d4dece0aee776a136427</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>colour_mask</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a4aa662177b306e9085f7ef20b3a6a2c1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t *</type>
      <name>ring_buffer_to_input_left_shifts</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ade696d20461dc712b7daafcbcad6ba4b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static void *</type>
      <name>saved_neuron_params_address</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>af0054ecd50a9d83ec3b87837779e061a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static void *</type>
      <name>current_source_address</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>a3ed312627afac83b5285c86756231886</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static void *</type>
      <name>saved_initial_values_address</name>
      <anchorfile>neuron_8c.html</anchorfile>
      <anchor>ac29f7d6b5e1d2e4b5afcf4c724b51d13</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron.h</name>
    <path>src/neuron/</path>
    <filename>neuron_8h.html</filename>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" import="no" module="no" objc="no">synapse_row.h</includes>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>neuron_initialise</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a0e3fd26136f3e14f31f40f95bf4e9e54</anchor>
      <arglist>(void *core_params_address, void *neuron_params_address, void *current_sources_address, void *recording_address, void *initial_values_address, uint32_t *n_rec_regions_used)</arglist>
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
      <anchor>a82283d81b442ae011e830b3c3ab7882b</anchor>
      <arglist>(uint32_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_pause</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>a09464219c59d7e79cbd4cf0acb9f96a1</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>neuron_transfer</name>
      <anchorfile>neuron_8h.html</anchorfile>
      <anchor>ab711f5128ef4a95c71bd123278bde9eb</anchor>
      <arglist>(weight_t *syns)</arglist>
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
      <anchor>a1352d326fa3e6bc9640b24bfd4cf2abd</anchor>
      <arglist>(uint32_t synapse_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_recording.h</name>
    <path>src/neuron/</path>
    <filename>neuron__recording_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <class kind="struct">recording_values_t</class>
    <class kind="struct">bitfield_values_t</class>
    <class kind="struct">recording_info_t</class>
    <class kind="struct">bitfield_info_t</class>
    <class kind="struct">neuron_recording_header_t</class>
    <member kind="define">
      <type>#define</type>
      <name>FLOOR_TO_2</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a403b173ad583ec922758a7edc380fa3c</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CEIL_TO_2</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>aa2d4795fc5236852254c8bebccde5764</anchor>
      <arglist></arglist>
    </member>
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
    <member kind="function" static="yes">
      <type>static void</type>
      <name>reset_record_counter</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a48e4d4f21167fadbe5b44ec1707677fe</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>bitfield_data_size</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>acf22d4e046f8216c065e3c77a5274f84</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>neuron_recording_read_in_elements</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ab1ce319a9907ceeca7fa4a77029bef5c</anchor>
      <arglist>(void *recording_address, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_reset</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a6ec6bcccf5cf769f8ea0c853ab0577e9</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>allocate_word_dtcm</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a8b7a478d22db76495934d689b0a32482</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>allocate_bitfield_dtcm</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>af48d91cdeaac5c1b26bf495746757f81</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>neuron_recording_initialise</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>acf13eda07e993e65ef639d2b70d4531b</anchor>
      <arglist>(void *recording_address, uint32_t n_neurons, uint32_t *n_rec_regions_used)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t **</type>
      <name>neuron_recording_indexes</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a7d71204655340d9946d301dd396b3cfe</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t **</type>
      <name>bitfield_recording_indexes</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a8e8050b4ec719ade7df406f544d1eb30</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static recording_info_t *</type>
      <name>recording_info</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a96a8e9a2f37a358a5264aadc6bb37263</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static bitfield_info_t *</type>
      <name>bitfield_info</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a2960fd20508bd11722265c5a5e2bebec</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint8_t **</type>
      <name>recording_values</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ac1ffd13a57545991775c1691ca0be09c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t **</type>
      <name>bitfield_values</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ab63f6c062cd231b9b383cdf19a09dd0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static volatile uint32_t</type>
      <name>n_recordings_outstanding</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>a629e0fd3d865713eb4c4ec5c0f0c5352</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static void *</type>
      <name>reset_address</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>ac4b03f54804a47d2b1d7f9086d42292a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>maths.h</name>
    <path>src/neuron/plasticity/stdp/</path>
    <filename>maths_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
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
      <anchor>a2d4508c79720a98c57d4cd9829a67af7</anchor>
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
    <path>src/neuron/plasticity/stdp/</path>
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
      <anchor>a475f1dc79565781cf76a637ec1b3fee7</anchor>
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
    <name>post_events_with_da.h</name>
    <path>src/neuron/plasticity/stdp/</path>
    <filename>post__events__with__da_8h.html</filename>
    <class kind="struct">nm_post_trace_t</class>
    <class kind="struct">post_event_history_t</class>
    <class kind="struct">post_event_window_t</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_POST_SYNAPTIC_EVENTS</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a3e545bee7f8f0a5c41ff9fe6a0536604</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_event_history</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a6deeebe9df2c90b608869bd1934af9db</anchor>
      <arglist>(const post_event_history_t *events)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_history_t *</type>
      <name>post_events_init_buffers</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a475f1dc79565781cf76a637ec1b3fee7</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_window_t</type>
      <name>post_events_get_window_delayed</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ac8fb2d0d29c873fd49869b215d81b60d</anchor>
      <arglist>(const post_event_history_t *events, uint32_t begin_time, uint32_t end_time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_window_t</type>
      <name>post_events_next</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a8b3f1431b102ab55a162d23e637d1a2f</anchor>
      <arglist>(post_event_window_t window)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>post_events_add</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a8e57e2579c38c2aec2037e8d8c6bb2bd</anchor>
      <arglist>(uint32_t time, post_event_history_t *events, post_trace_t post_trace, int16_t dopamine_trace, bool dopamine)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_delayed_window_events</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ae8696ad6309cecd361c85e5c35bc4aab</anchor>
      <arglist>(const post_event_history_t *post_event_history, uint32_t begin_time, uint32_t end_time, uint32_t delay_dendritic)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>stdp_typedefs.h</name>
    <path>src/neuron/plasticity/stdp/</path>
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
    <member kind="define">
      <type>#define</type>
      <name>S1615_TO_STDP_RIGHT_SHIFT</name>
      <anchorfile>stdp__typedefs_8h.html</anchorfile>
      <anchor>ae91c823fd0df69e3b7badc884f3b3974</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>mul_accum_fixed</name>
      <anchorfile>stdp__typedefs_8h.html</anchorfile>
      <anchor>a904dbd1f4e3e796d09b3af089af85848</anchor>
      <arglist>(accum a, int32_t stdp_fixed)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_stdp_common.h</name>
    <path>src/neuron/plasticity/stdp/</path>
    <filename>synapse__dynamics__stdp__common_8h.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="no" import="no" module="no" objc="no">neuron/synapses.h</includes>
    <includes id="maths_8h" name="maths.h" local="yes" import="no" module="no" objc="no">maths.h</includes>
    <includes id="post__events_8h" name="post_events.h" local="yes" import="no" module="no" objc="no">post_events.h</includes>
    <includes id="weight_8h" name="weight.h" local="yes" import="no" module="no" objc="no">weight_dependence/weight.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing_dependence/timing.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="no" import="no" module="no" objc="no">neuron/plasticity/synapse_dynamics.h</includes>
    <class kind="struct">pre_event_history_t</class>
    <class kind="struct">stdp_params</class>
    <class kind="struct">fixed_stdp_synapse</class>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a24b755e1d96fcab4e950b83796376e75</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a540b2206e6909e8e88c3a98a47ddcb2a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static control_t</type>
      <name>control_conversion</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a06f2e2d805f0d8aa8b3ca7b687f24a24</anchor>
      <arglist>(uint32_t id, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_n_connections_in_row</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>aca5fc1011c991013823ad76158bf57f3</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static stdp_params</type>
      <name>params</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a159669347528cd4f88c368d0d33e4670</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static post_event_history_t *</type>
      <name>post_event_history</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a9738c22cad44349036699b2383355540</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a9e7456ba7de4fa401d09c84644229f91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a865d0cf426d384be02e8f07b34b05e31</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_stdp_izhikevich_neuromodulation.c</name>
    <path>src/neuron/plasticity/stdp/</path>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <includes id="post__events__with__da_8h" name="post_events_with_da.h" local="yes" import="no" module="no" objc="no">post_events_with_da.h</includes>
    <includes id="synapse__dynamics__stdp__common_8h" name="synapse_dynamics_stdp_common.h" local="yes" import="no" module="no" objc="no">synapse_dynamics_stdp_common.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="yes" import="no" module="no" objc="no">stdp_typedefs.h</includes>
    <class kind="struct">neuromodulation_data_t</class>
    <class kind="struct">neuromodulated_synapse_t</class>
    <class kind="struct">nm_update_state_t</class>
    <class kind="struct">nm_final_state_t</class>
    <class kind="struct">synapse_row_plastic_data_t</class>
    <class kind="struct">nm_params_t</class>
    <class kind="union">synapse_row_plastic_data_t.__unnamed10__</class>
    <class kind="struct">synapse_row_plastic_data_t.__unnamed10__.__unnamed12__</class>
    <member kind="function" static="yes">
      <type>static nm_final_state_t</type>
      <name>izhikevich_neuromodulation_plasticity_update_synapse</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>aeea32132c2a3d9f4bce71f846d2f9ec7</anchor>
      <arglist>(const uint32_t time, const uint32_t last_pre_time, const pre_trace_t last_pre_trace, const pre_trace_t new_pre_trace, const uint32_t delay_dendritic, const uint32_t delay_axonal, nm_update_state_t current_state, const post_event_history_t *post_event_history)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_print_plastic_synapses</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>ac0dc7f1b3f6348db279fbad8c8040b1c</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>sparse_axonal_delay</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>abade6b73a469c1ff0e54366f065343e5</anchor>
      <arglist>(uint32_t x)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>afaa7bb6d8e094b3447e52c9b94eebcbd</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_address, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time, uint32_t colour_delay, bool *write_back)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_find_neuron</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a5893fd33bdac3b991ecb7cb61feb4188</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay, uint32_t *offset, uint32_t *synapse_type)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_remove_neuron</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>af3e517401d329d33f14b0ba70743e127</anchor>
      <arglist>(uint32_t offset, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_add_neuron</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>ac877b6394f131f1944a720c387af6ac1</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t weight, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>skipped_synapses</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>af61f61aa805ba87019bb5f3f8e44bf0f</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_stdp_mad_impl.c</name>
    <path>src/neuron/plasticity/stdp/</path>
    <filename>synapse__dynamics__stdp__mad__impl_8c.html</filename>
    <includes id="post__events_8h" name="post_events.h" local="yes" import="no" module="no" objc="no">post_events.h</includes>
    <includes id="synapse__dynamics__stdp__common_8h" name="synapse_dynamics_stdp_common.h" local="yes" import="no" module="no" objc="no">synapse_dynamics_stdp_common.h</includes>
    <class kind="struct">synapse_row_plastic_data_t</class>
    <member kind="function" static="yes">
      <type>static final_state_t</type>
      <name>plasticity_update_synapse</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>aa195e42fb2e365fe51384e2ef8a95ec8</anchor>
      <arglist>(const uint32_t time, const uint32_t last_pre_time, const pre_trace_t last_pre_trace, const pre_trace_t new_pre_trace, const uint32_t delay_dendritic, const uint32_t delay_axonal, update_state_t current_state, const post_event_history_t *post_event_history)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
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
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>afaa7bb6d8e094b3447e52c9b94eebcbd</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_address, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time, uint32_t colour_delay, bool *write_back)</arglist>
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
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_add_neuron</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>ac877b6394f131f1944a720c387af6ac1</anchor>
      <arglist>(uint32_t id, synaptic_row_t row, weight_t weight, uint32_t delay, uint32_t type)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>skipped_synapses</name>
      <anchorfile>synapse__dynamics__stdp__mad__impl_8c.html</anchorfile>
      <anchor>af61f61aa805ba87019bb5f3f8e44bf0f</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure.h</name>
    <path>src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight.h</includes>
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
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_structure_decay_weight</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>a68ea811bcff6f1ffbd471cf846e04347</anchor>
      <arglist>(update_state_t *state, uint32_t decay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>synapse_structure_get_update_weight</name>
      <anchorfile>synapse__structure_8h.html</anchorfile>
      <anchor>a3a382e1f377e5359969deaffc03478f0</anchor>
      <arglist>(update_state_t state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_structure_weight_accumulator_impl.h</name>
    <path>src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__accumulator__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" import="no" module="no" objc="no">synapse_structure.h</includes>
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
    <path>src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" import="no" module="no" objc="no">synapse_structure.h</includes>
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
    <path>src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__state__accumulator__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" import="no" module="no" objc="no">synapse_structure.h</includes>
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
    <path>src/neuron/plasticity/stdp/synapse_structure/</path>
    <filename>synapse__structure__weight__state__accumulator__window__impl_8h.html</filename>
    <includes id="synapse__structure_8h" name="synapse_structure.h" local="yes" import="no" module="no" objc="no">synapse_structure.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>random__util_8h.html</filename>
    <member kind="variable" static="yes">
      <type>static mars_kiss64_seed_t</type>
      <name>seed</name>
      <anchorfile>random__util_8h.html</anchorfile>
      <anchor>a242fd815ccc9f4b3ad34154405da64c6</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>timing.h</name>
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing_8h.html</filename>
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
      <type>static post_trace_t</type>
      <name>timing_decay_post</name>
      <anchorfile>timing_8h.html</anchorfile>
      <anchor>a2bea916966f35c743fa3fafab145f69d</anchor>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__nearest__pair__impl_8c.html</filename>
    <includes id="timing__nearest__pair__impl_8h" name="timing_nearest_pair_impl.h" local="yes" import="no" module="no" objc="no">timing_nearest_pair_impl.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__nearest__pair__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pair__impl_8c.html</filename>
    <includes id="timing__pair__impl_8h" name="timing_pair_impl.h" local="yes" import="no" module="no" objc="no">timing_pair_impl.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pair__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pfister__triplet__impl_8c.html</filename>
    <includes id="timing__pfister__triplet__impl_8h" name="timing_pfister_triplet_impl.h" local="yes" import="no" module="no" objc="no">timing_pfister_triplet_impl.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__pfister__triplet__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__two__term_8h" name="weight_two_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_two_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__common_8h.html</filename>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="random__util_8h" name="random_util.h" local="yes" import="no" module="no" objc="no">random_util.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__dual__fsm__impl_8c.html</filename>
    <includes id="timing__recurrent__dual__fsm__impl_8h" name="timing_recurrent_dual_fsm_impl.h" local="yes" import="no" module="no" objc="no">timing_recurrent_dual_fsm_impl.h</includes>
    <class kind="struct">dual_fsm_config_t</class>
    <member kind="function">
      <type>uint32_t *</type>
      <name>timing_initialise</name>
      <anchorfile>timing__recurrent__dual__fsm__impl_8c.html</anchorfile>
      <anchor>a8d3c98aeb95e5c738e01b92f0645c090</anchor>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__dual__fsm__impl_8h.html</filename>
    <includes id="synapse__structure__weight__accumulator__impl_8h" name="synapse_structure_weight_accumulator_impl.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="random__util_8h" name="random_util.h" local="yes" import="no" module="no" objc="no">random_util.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__pre__stochastic__impl_8c.html</filename>
    <includes id="timing__recurrent__pre__stochastic__impl_8h" name="timing_recurrent_pre_stochastic_impl.h" local="yes" import="no" module="no" objc="no">timing_recurrent_pre_stochastic_impl.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__recurrent__pre__stochastic__impl_8h.html</filename>
    <includes id="timing__recurrent__common_8h" name="timing_recurrent_common.h" local="yes" import="no" module="no" objc="no">timing_recurrent_common.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__vogels__2011__impl_8c.html</filename>
    <includes id="timing__vogels__2011__impl_8h" name="timing_vogels_2011_impl.h" local="yes" import="no" module="no" objc="no">timing_vogels_2011_impl.h</includes>
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
    <path>src/neuron/plasticity/stdp/timing_dependence/</path>
    <filename>timing__vogels__2011__impl_8h.html</filename>
    <includes id="synapse__structure__weight__impl_8h" name="synapse_structure_weight_impl.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h</includes>
    <includes id="timing_8h" name="timing.h" local="yes" import="no" module="no" objc="no">timing.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/weight_dependence/weight_one_term.h</includes>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
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
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
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
    <member kind="function" static="yes">
      <type>static void</type>
      <name>weight_decay</name>
      <anchorfile>weight_8h.html</anchorfile>
      <anchor>a972034e6079f096790f3792953e81244</anchor>
      <arglist>(weight_state_t *state, int32_t decay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>weight_get_update</name>
      <anchorfile>weight_8h.html</anchorfile>
      <anchor>ac708061b0c6931efe714b246ebea52b8</anchor>
      <arglist>(weight_state_t state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_one_term_impl.c</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__one__term__impl_8c.html</filename>
    <includes id="weight__additive__one__term__impl_8h" name="weight_additive_one_term_impl.h" local="yes" import="no" module="no" objc="no">weight_additive_one_term_impl.h</includes>
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
    <member kind="variable">
      <type>uint32_t *</type>
      <name>weight_shift</name>
      <anchorfile>weight__additive__one__term__impl_8c.html</anchorfile>
      <anchor>a62ffb30557cf5bc13faca83484cac280</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_one_term_impl.h</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__one__term__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="yes" import="no" module="no" objc="no">weight_one_term.h</includes>
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
      <anchor>ad2b085719288697a428d2106581e2540</anchor>
      <arglist>(weight_state_t state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_two_term_impl.c</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__two__term__impl_8c.html</filename>
    <includes id="weight__additive__two__term__impl_8h" name="weight_additive_two_term_impl.h" local="yes" import="no" module="no" objc="no">weight_additive_two_term_impl.h</includes>
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
    <member kind="variable">
      <type>uint32_t *</type>
      <name>weight_shift</name>
      <anchorfile>weight__additive__two__term__impl_8c.html</anchorfile>
      <anchor>a62ffb30557cf5bc13faca83484cac280</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_additive_two_term_impl.h</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__additive__two__term__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <includes id="weight__two__term_8h" name="weight_two_term.h" local="yes" import="no" module="no" objc="no">weight_two_term.h</includes>
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
      <anchor>ad2b085719288697a428d2106581e2540</anchor>
      <arglist>(weight_state_t state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_multiplicative_impl.c</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__multiplicative__impl_8c.html</filename>
    <includes id="weight__multiplicative__impl_8h" name="weight_multiplicative_impl.h" local="yes" import="no" module="no" objc="no">weight_multiplicative_impl.h</includes>
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
      <name>weight_shift</name>
      <anchorfile>weight__multiplicative__impl_8c.html</anchorfile>
      <anchor>a62ffb30557cf5bc13faca83484cac280</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_multiplicative_impl.h</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__multiplicative__impl_8h.html</filename>
    <includes id="maths_8h" name="maths.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/maths.h</includes>
    <includes id="stdp__typedefs_8h" name="stdp_typedefs.h" local="no" import="no" module="no" objc="no">neuron/plasticity/stdp/stdp_typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <includes id="weight__one__term_8h" name="weight_one_term.h" local="yes" import="no" module="no" objc="no">weight_one_term.h</includes>
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
      <anchor>ad2b085719288697a428d2106581e2540</anchor>
      <arglist>(weight_state_t state)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>weight_one_term.h</name>
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__one__term_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="yes" import="no" module="no" objc="no">weight.h</includes>
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
    <path>src/neuron/plasticity/stdp/weight_dependence/</path>
    <filename>weight__two__term_8h.html</filename>
    <includes id="weight_8h" name="weight.h" local="yes" import="no" module="no" objc="no">weight.h</includes>
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
    <path>src/neuron/plasticity/</path>
    <filename>synapse__dynamics_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
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
      <anchor>a64f836033fa394ddca67b3e12a23b45e</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time, uint32_t colour_delay, bool *write_back)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics_8h.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
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
    <path>src/neuron/plasticity/</path>
    <filename>synapse__dynamics__static__impl_8c.html</filename>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" import="no" module="no" objc="no">synapse_dynamics.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="no" import="no" module="no" objc="no">neuron/synapses.h</includes>
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
      <anchor>aaefbee0b2c6af4b88af6bfb696eda140</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_data, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffer, uint32_t time, uint32_t colour_delay, bool *write_back)</arglist>
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
  </compound>
  <compound kind="file">
    <name>post_events_with_weight_change.h</name>
    <path>src/neuron/plasticity/weight_change/</path>
    <filename>post__events__with__weight__change_8h.html</filename>
    <class kind="struct">update_post_trace_t</class>
    <class kind="struct">post_event_history_t</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_EVENTS</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>ae42954bb8545d24e3e9dcde5920c9a0b</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static post_event_history_t *</type>
      <name>post_events_init_buffers</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a475f1dc79565781cf76a637ec1b3fee7</anchor>
      <arglist>(uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>post_events_add</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>aad9a77e8a8c91c66ebdcba29d79fd088</anchor>
      <arglist>(post_event_history_t *events, uint16_t weight_change, uint32_t pre_spike, uint16_t synapse_type)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_dynamics_external_weight_change.c</name>
    <path>src/neuron/plasticity/weight_change/</path>
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <includes id="post__events__with__weight__change_8h" name="post_events_with_weight_change.h" local="yes" import="no" module="no" objc="no">post_events_with_weight_change.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="no" import="no" module="no" objc="no">neuron/synapses.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="no" import="no" module="no" objc="no">neuron/plasticity/synapse_dynamics.h</includes>
    <class kind="struct">limits</class>
    <class kind="struct">change_params</class>
    <class kind="struct">updatable_synapse_t</class>
    <class kind="struct">synapse_row_plastic_data_t</class>
    <class kind="struct">fixed_stdp_synapse</class>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_initialise</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a4a1c98d660ba6a17d4678ae9ef2a5526</anchor>
      <arglist>(address_t address, uint32_t n_neurons, uint32_t n_synapse_types, uint32_t *ring_buffer_to_input_buffer_left_shifts)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapse_dynamics_process_post_synaptic_event</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a5087bc7e79f5dc3850f73239c5c463a3</anchor>
      <arglist>(uint32_t time, index_t neuron_index)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapse_dynamics_process_plastic_synapses</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>afaa7bb6d8e094b3447e52c9b94eebcbd</anchor>
      <arglist>(synapse_row_plastic_data_t *plastic_region_address, synapse_row_fixed_part_t *fixed_region, weight_t *ring_buffers, uint32_t time, uint32_t colour_delay, bool *write_back)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a24b755e1d96fcab4e950b83796376e75</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synapse_dynamics_get_plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a540b2206e6909e8e88c3a98a47ddcb2a</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static post_event_history_t *</type>
      <name>post_event_history</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a9738c22cad44349036699b2383355540</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>num_plastic_pre_synaptic_events</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a9e7456ba7de4fa401d09c84644229f91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>plastic_saturation_count</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a865d0cf426d384be02e8f07b34b05e31</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static change_params *</type>
      <name>params</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>adf3ff410ba03015a151ba944594850b8</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>population_table.h</name>
    <path>src/neuron/population_table/</path>
    <filename>population__table_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <class kind="struct">master_population_table_entry</class>
    <class kind="struct">address_list_entry</class>
    <class kind="struct">pop_table_config_t</class>
    <class kind="struct">pop_table_lookup_result_t</class>
    <member kind="define">
      <type>#define</type>
      <name>BITS_PER_WORD</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>af859a98f57110e5243e8f0541319e43b</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>TOP_BIT_IN_WORD</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a76abab9c83287abfbdde2324b659b836</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>NOT_IN_MASTER_POP_TABLE_FLAG</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a5f369817d958cb4c367752b5558957b1</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>N_ADDRESS_BITS</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a2233d5046582aeea3564c6ec3e72c553</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>INDIRECT_ADDRESS_SHIFT</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a36896ff3554f8b8ee7fe1599ec6c26f5</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>INVALID_ADDRESS</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ac0e87c1d66cacc61454b23cdc12ff764</anchor>
      <arglist></arglist>
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
    <member kind="variable">
      <type>uint16_t</type>
      <name>items_to_go</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>aebd5b17aab1bbe44fa564e8786f84d94</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_offset</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a071de88b0691d4747c55dbea8cc58f86</anchor>
      <arglist>(address_list_entry entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_address</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a2916b1e1b3368cce2257f3a2d2babd11</anchor>
      <arglist>(address_list_entry entry, uint32_t addr)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_row_length</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a44d4641d18cf8073f34f171a7e9a0f54</anchor>
      <arglist>(address_list_entry entry)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_index</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>aa2d4dd26fcbfb2f760cc5ec9c021e475</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_core_sum</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ac6d62fa8b2be8dfcb6c5ff7c9ff9d7aa</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_neuron_id</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ab08d6807fc8fd46ed5f70a8bd14a5a93</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>get_local_neuron_id</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a48c705b7db3ec689ae14c6173df1de60</anchor>
      <arglist>(master_population_table_entry entry, spike_t spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>get_row_addr_and_size</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a45f32a7841183cdb7aab2be2a91fd6ba</anchor>
      <arglist>(address_list_entry item, uint32_t synaptic_rows_base_address, uint32_t neuron_id, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_setup</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a0b783bdc820853519d04fe41adb0b7de</anchor>
      <arglist>(address_t table_address, uint32_t *row_max_n_words, uint32_t *master_pop_table_length, master_population_table_entry **master_pop_table, address_list_entry **address_list)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ac894fca012fcf12a7730d360f65e535b</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, uint32_t *row_max_n_words)</arglist>
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
      <anchor>a8b234fa7be2bc90125b4d3f7644de260</anchor>
      <arglist>(spike_t spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>population_table_is_next</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a6af50f83e29bc2f5340724898921df93</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a1027d2b00f18099c520d5ac97df369ae</anchor>
      <arglist>(spike_t *spike, pop_table_lookup_result_t *result)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>population_table_binary_search_impl.c</name>
    <path>src/neuron/population_table/</path>
    <filename>population__table__binary__search__impl_8c.html</filename>
    <includes id="population__table_8h" name="population_table.h" local="yes" import="no" module="no" objc="no">population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_master_population_table</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a3c2c10dcc54c9ec95a730e4c1324a2c5</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>print_bitfields</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1f7ee4914c85908186b0301d9deaba4c</anchor>
      <arglist>(uint32_t mp_i, filter_info_t *filters)</arglist>
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
      <name>population_table_setup</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a0b783bdc820853519d04fe41adb0b7de</anchor>
      <arglist>(address_t table_address, uint32_t *row_max_n_words, uint32_t *master_pop_table_length, master_population_table_entry **master_pop_table, address_list_entry **address_list)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac894fca012fcf12a7730d360f65e535b</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, uint32_t *row_max_n_words)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_first_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a8b234fa7be2bc90125b4d3f7644de260</anchor>
      <arglist>(spike_t spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1027d2b00f18099c520d5ac97df369ae</anchor>
      <arglist>(spike_t *spike, pop_table_lookup_result_t *result)</arglist>
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
      <type>static spike_t</type>
      <name>last_spike</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>af5f8c1b781901d417e09126b75d60140</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>last_colour</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a2fc529e22b2269c4c8d9e75152288a94</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>last_colour_mask</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a879944bd1ee487bf01f13a19d4e42be6</anchor>
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
    <member kind="variable">
      <type>uint16_t</type>
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
    <member kind="function">
      <type>bool</type>
      <name>population_table_initialise</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>ac894fca012fcf12a7730d360f65e535b</anchor>
      <arglist>(address_t table_address, address_t synapse_rows_address, uint32_t *row_max_n_words)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_first_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a8b234fa7be2bc90125b4d3f7644de260</anchor>
      <arglist>(spike_t spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>population_table_get_next_address</name>
      <anchorfile>population__table__binary__search__impl_8c.html</anchorfile>
      <anchor>a1027d2b00f18099c520d5ac97df369ae</anchor>
      <arglist>(spike_t *spike, pop_table_lookup_result_t *result)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>profile_tags.h</name>
    <path>src/neuron/</path>
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
    <path>src/spike_source/poisson/</path>
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
    <path>src/neuron/</path>
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
      <name>CORE_PARAMS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a0d3388e5865664c61df9083946894849</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NEURON_PARAMS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a0763e3d54f2b5ccc90f6ba223d6b68e8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CURRENT_SOURCE_PARAMS_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6af43f04c9fca7f11ed6deb850fc90b223</anchor>
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
      <name>NEURON_BUILDER_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6adfa066c343d11dbd1ec0909bad0d0319</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BIT_FIELD_FILTER_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a34f5ecbcfa6c6469d2e5d1fbbae9a55b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>RECORDING_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a1fcdb0acbaceba25c8b18313a1efbcbd</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>INITIAL_VALUES_REGION</name>
      <anchorfile>regions_8h.html</anchorfile>
      <anchor>a94cb8426c71368d0a24cf95fcc70a3d6a1b7dad0611f796bf47478691cacd5ddd</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>spike_processing.c</name>
    <path>src/neuron/</path>
    <filename>spike__processing_8c.html</filename>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" import="no" module="no" objc="no">spike_processing.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="yes" import="no" module="no" objc="no">population_table/population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" import="no" module="no" objc="no">synapse_row.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="yes" import="no" module="no" objc="no">synapses.h</includes>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" import="no" module="no" objc="no">structural_plasticity/synaptogenesis_dynamics.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" import="no" module="no" objc="no">common/in_spikes.h</includes>
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
      <anchor>a7864846d55171d96eba62635e0d61a49</anchor>
      <arglist>(spike_t spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>is_something_to_do</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>aabdb3130b5c92cc4badbc4ea8109b079</anchor>
      <arglist>(spike_t *spike, pop_table_lookup_result_t *result, uint32_t *n_rewire, uint32_t *n_process_spike)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>setup_synaptic_dma_read</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a28d3a38d21ac9445175abd0ca06abd04</anchor>
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
      <name>start_dma_loop</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a15c13024e662ea8b6f65f6a7d4e47d6b</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>multicast_packet_received_callback</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a626c5a1b73ac86ddd701e51b776359c7</anchor>
      <arglist>(uint key, uint unused)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>multicast_packet_pl_received_callback</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>a83647c826b1e101818defc30a3ab2f09</anchor>
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
      <type>void</type>
      <name>spike_processing_store_provenance</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>abb96759bd7b125d191bd87e7055da319</anchor>
      <arglist>(struct spike_processing_provenance *prov)</arglist>
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
      <type>static struct @13</type>
      <name>p_per_ts_struct</name>
      <anchorfile>spike__processing_8c.html</anchorfile>
      <anchor>ae80be56b85b664a136cb072f52835c12</anchor>
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
    <path>src/neuron/</path>
    <filename>spike__processing_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" import="no" module="no" objc="no">common/in_spikes.h</includes>
    <class kind="struct">spike_processing_provenance</class>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_initialise</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a9bca959f2f789a64fc217e2751533e96</anchor>
      <arglist>(size_t row_max_n_bytes, uint mc_packet_callback_priority, uint user_event_priority, uint incoming_spike_buffer_size, bool clear_input_buffers_of_late_packets_init, uint32_t packets_per_timestep_region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_store_provenance</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>abb96759bd7b125d191bd87e7055da319</anchor>
      <arglist>(struct spike_processing_provenance *prov)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_do_rewiring</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a392325c1b5bc32c222df0a35d3dcfad3</anchor>
      <arglist>(int number_of_rewires)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_clear_input_buffer</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>aa0ddebf0b174a40cd3406916d98f6352</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>spike_processing_fast.h</name>
    <path>src/neuron/</path>
    <filename>spike__processing__fast_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" import="no" module="no" objc="no">common/in_spikes.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" import="no" module="no" objc="no">synapse_row.h</includes>
    <class kind="struct">sdram_config</class>
    <class kind="struct">key_config</class>
    <class kind="struct">spike_processing_fast_provenance</class>
    <member kind="function">
      <type>bool</type>
      <name>spike_processing_fast_initialise</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a9675fd66449aa60f08c39561c803ccf9</anchor>
      <arglist>(uint32_t row_max_n_words, uint32_t spike_buffer_size, bool discard_late_packets, uint32_t pkts_per_ts_rec_region, uint32_t multicast_priority, struct sdram_config sdram_inputs_param, struct key_config key_config_param, weight_t *ring_buffers_param)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_fast_time_step_loop</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a3feb6ea173c87c2b68c1606b751dbc47</anchor>
      <arglist>(uint32_t time, uint32_t n_rewires)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>spike_processing_fast_store_provenance</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a732f158512c578360e7158b13be86f22</anchor>
      <arglist>(struct spike_processing_fast_provenance *prov)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>elimination.h</name>
    <path>src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination_8h.html</filename>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" import="no" module="no" objc="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="function">
      <type>elimination_params_t *</type>
      <name>synaptogenesis_elimination_init</name>
      <anchorfile>elimination_8h.html</anchorfile>
      <anchor>a42eff07e9e8274d24a9bd98063bc8d32</anchor>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination__random__by__weight__impl_8c.html</filename>
    <includes id="elimination__random__by__weight__impl_8h" name="elimination_random_by_weight_impl.h" local="yes" import="no" module="no" objc="no">elimination_random_by_weight_impl.h</includes>
    <member kind="function">
      <type>elimination_params_t *</type>
      <name>synaptogenesis_elimination_init</name>
      <anchorfile>elimination__random__by__weight__impl_8c.html</anchorfile>
      <anchor>a42eff07e9e8274d24a9bd98063bc8d32</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>elimination_random_by_weight_impl.h</name>
    <path>src/neuron/structural_plasticity/synaptogenesis/elimination/</path>
    <filename>elimination__random__by__weight__impl_8h.html</filename>
    <includes id="elimination_8h" name="elimination.h" local="yes" import="no" module="no" objc="no">elimination.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation_8h.html</filename>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" import="no" module="no" objc="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="function">
      <type>formation_params_t *</type>
      <name>synaptogenesis_formation_init</name>
      <anchorfile>formation_8h.html</anchorfile>
      <anchor>a7010dcc32e8e0c91a64262d0b36de237</anchor>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation__distance__dependent__impl_8c.html</filename>
    <includes id="formation__distance__dependent__impl_8h" name="formation_distance_dependent_impl.h" local="yes" import="no" module="no" objc="no">formation_distance_dependent_impl.h</includes>
    <member kind="function">
      <type>formation_params_t *</type>
      <name>synaptogenesis_formation_init</name>
      <anchorfile>formation__distance__dependent__impl_8c.html</anchorfile>
      <anchor>a7010dcc32e8e0c91a64262d0b36de237</anchor>
      <arglist>(uint8_t **data)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>formation_distance_dependent_impl.h</name>
    <path>src/neuron/structural_plasticity/synaptogenesis/formation/</path>
    <filename>formation__distance__dependent__impl_8h.html</filename>
    <includes id="formation_8h" name="formation.h" local="yes" import="no" module="no" objc="no">formation.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>last__neuron__selection__impl_8c.html</filename>
    <includes id="last__neuron__selection__impl_8h" name="last_neuron_selection_impl.h" local="yes" import="no" module="no" objc="no">last_neuron_selection_impl.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>last__neuron__selection__impl_8h.html</filename>
    <includes id="partner_8h" name="partner.h" local="yes" import="no" module="no" objc="no">partner.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="no" import="no" module="no" objc="no">neuron/spike_processing.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>partner_8h.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="no" import="no" module="no" objc="no">neuron/synapses.h</includes>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" import="no" module="no" objc="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>random__selection__impl_8c.html</filename>
    <includes id="random__selection__impl_8h" name="random_selection_impl.h" local="yes" import="no" module="no" objc="no">random_selection_impl.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/partner_selection/</path>
    <filename>random__selection__impl_8h.html</filename>
    <includes id="partner_8h" name="partner.h" local="yes" import="no" module="no" objc="no">partner.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="no" import="no" module="no" objc="no">neuron/spike_processing.h</includes>
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
    <path>src/neuron/structural_plasticity/synaptogenesis/</path>
    <filename>sp__structs_8h.html</filename>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="no" import="no" module="no" objc="no">neuron/plasticity/synapse_dynamics.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
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
      <anchor>a3e9692a85b7565cab44cf06037c50add</anchor>
      <arglist>(address_t sdram_sp_address, rewiring_data_t *rewiring_data, pre_pop_info_table_t *pre_info, post_to_pre_entry **post_to_pre_table)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>topographic_map_impl.c</name>
    <path>src/neuron/structural_plasticity/synaptogenesis/</path>
    <filename>topographic__map__impl_8c.html</filename>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="no" import="no" module="no" objc="no">neuron/structural_plasticity/synaptogenesis_dynamics.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="no" import="no" module="no" objc="no">neuron/population_table/population_table.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <includes id="synapses_8h" name="synapses.h" local="no" import="no" module="no" objc="no">neuron/synapses.h</includes>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="partner_8h" name="partner.h" local="yes" import="no" module="no" objc="no">partner_selection/partner.h</includes>
    <includes id="elimination_8h" name="elimination.h" local="yes" import="no" module="no" objc="no">elimination/elimination.h</includes>
    <includes id="formation_8h" name="formation.h" local="yes" import="no" module="no" objc="no">formation/formation.h</includes>
    <class kind="struct">structural_recording_values_t</class>
    <member kind="define">
      <type>#define</type>
      <name>ID_SHIFT</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a133e523294833f2163af1d9c289b755e</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>PRE_ID_SHIFT</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>ac72a3940dec756858cef5e5f77cdaef8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ELIM_FLAG</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aba01db17f4a2bfbc3db60dc172972a25ae6ee7be3fbd9056d0d38e36762f50da7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FORM_FLAG</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aba01db17f4a2bfbc3db60dc172972a25a77fb1f2705b16e5d115198616780afb6</anchor>
      <arglist></arglist>
    </member>
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
      <anchor>ad4efac9c7152c9f89d5c7ae05fb7ab53</anchor>
      <arglist>(address_t sdram_sp_address, uint32_t *recording_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a02d8b50126664d08cc5af3b42058a75f</anchor>
      <arglist>(uint32_t time, spike_t *spike, pop_table_lookup_result_t *result)</arglist>
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
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synaptogenesis_n_updates</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a8a0a440cd05af069b57b447a9cc8ca93</anchor>
      <arglist>(void)</arglist>
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
    <member kind="variable">
      <type>uint32_t</type>
      <name>rewiring_recording_index</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a4a10759c0e9d46f40f5bdce22d00d454</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>structural_recording_values_t</type>
      <name>structural_recording_values</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>a86abfa547d5ce057edf3ec291b2d0255</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>last_rewiring_time</name>
      <anchorfile>topographic__map__impl_8c.html</anchorfile>
      <anchor>aa6d38210641f6270b8c8df58e53cd885</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synaptogenesis_dynamics.h</name>
    <path>src/neuron/structural_plasticity/</path>
    <filename>synaptogenesis__dynamics_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="no" import="no" module="no" objc="no">neuron/population_table/population_table.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_initialise</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>ad4efac9c7152c9f89d5c7ae05fb7ab53</anchor>
      <arglist>(address_t sdram_sp_address, uint32_t *recording_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a02d8b50126664d08cc5af3b42058a75f</anchor>
      <arglist>(uint32_t time, spike_t *spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_row_restructure</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>ac97a88bbadb38fa4d4a67aa86aa615c8</anchor>
      <arglist>(uint32_t time, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synaptogenesis_n_updates</name>
      <anchorfile>synaptogenesis__dynamics_8h.html</anchorfile>
      <anchor>a8a0a440cd05af069b57b447a9cc8ca93</anchor>
      <arglist>(void)</arglist>
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
    <path>src/neuron/structural_plasticity/</path>
    <filename>synaptogenesis__dynamics__static__impl_8c.html</filename>
    <includes id="synaptogenesis__dynamics_8h" name="synaptogenesis_dynamics.h" local="yes" import="no" module="no" objc="no">synaptogenesis_dynamics.h</includes>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_initialise</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>ad4efac9c7152c9f89d5c7ae05fb7ab53</anchor>
      <arglist>(address_t sdram_sp_address, uint32_t *recording_regions_used)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_dynamics_rewire</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a02d8b50126664d08cc5af3b42058a75f</anchor>
      <arglist>(uint32_t time, spike_t *spike, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synaptogenesis_row_restructure</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>ac97a88bbadb38fa4d4a67aa86aa615c8</anchor>
      <arglist>(uint32_t time, synaptic_row_t row)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synaptogenesis_spike_received</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a51fae9acd15ca3ad50a61ce734de93c2</anchor>
      <arglist>(uint32_t time, spike_t spike)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>synaptogenesis_n_updates</name>
      <anchorfile>synaptogenesis__dynamics__static__impl_8c.html</anchorfile>
      <anchor>a8a0a440cd05af069b57b447a9cc8ca93</anchor>
      <arglist>(void)</arglist>
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
    <path>src/neuron/</path>
    <filename>synapse__row_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
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
      <anchor>aafcc2d465fcf3b6078e5b3849236a64d</anchor>
      <arglist>(synaptic_row_t row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static synapse_row_fixed_part_t *</type>
      <name>synapse_row_fixed_region</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a7f3f94b3292d8ddfe183e6bb69141ba4</anchor>
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
      <anchor>a8050fb8998443314a1e2c92f90ff6d5c</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t *</type>
      <name>synapse_row_fixed_weight_controls</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>abc9e3dfe4b3142f2f6f23309d499eac9</anchor>
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
      <anchor>aa94acd48786374e44bc977f6fe4baa36</anchor>
      <arglist>(uint32_t x, uint32_t synapse_type_index_bits, uint32_t synapse_delay_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static weight_t</type>
      <name>synapse_row_sparse_weight</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>af7eb0b5869f5256cf8a1343860d8aa21</anchor>
      <arglist>(uint32_t x)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t</type>
      <name>synapse_row_convert_weight_to_input</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ae4e41ab174db01514418797dd28118e6</anchor>
      <arglist>(weight_t weight, uint32_t left_shift)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_get_ring_buffer_index</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>ada89d2ef336aea90633c0db125fe5685</anchor>
      <arglist>(uint32_t simulation_timestep, uint32_t synapse_type_index, uint32_t neuron_index, uint32_t synapse_type_index_bits, uint32_t synapse_index_bits, uint32_t synapse_delay_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_get_ring_buffer_index_time_0</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>afde1da28f9000c4691897c29e64568b7</anchor>
      <arglist>(uint32_t synapse_type_index, uint32_t neuron_index, uint32_t synapse_index_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_get_first_ring_buffer_index</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a11682ae0a4ca3bb9004b9c2ee829a49a</anchor>
      <arglist>(uint32_t simulation_timestep, uint32_t synapse_type_index_bits, int32_t synapse_delay_mask)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static index_t</type>
      <name>synapse_row_get_ring_buffer_index_combined</name>
      <anchorfile>synapse__row_8h.html</anchorfile>
      <anchor>a8e60d389a3182e12627b3eec89a9dee5</anchor>
      <arglist>(uint32_t simulation_timestep, uint32_t combined_synapse_neuron_index, uint32_t synapse_type_index_bits, uint32_t synapse_delay_mask)</arglist>
    </member>
    <docanchor file="synapse__row_8h.html" title="Synapse Row Representation">row</docanchor>
    <docanchor file="synapse__row_8h.html" title="Data Structure">matrix</docanchor>
    <docanchor file="synapse__row_8h.html" title="Fixed and Fixed-Plastic Regions">fixed</docanchor>
  </compound>
  <compound kind="file">
    <name>exp_synapse_utils.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>exp__synapse__utils_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" import="no" module="no" objc="no">neuron/decay.h</includes>
    <class kind="struct">exp_params_t</class>
    <class kind="struct">exp_state_t</class>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>decay_and_init</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>a520234c2d6b83476eb4ccd9b9d0090c6</anchor>
      <arglist>(exp_state_t *state, exp_params_t *params, REAL time_step_ms, uint32_t n_steps_per_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>exp_shaping</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>ac13fc21295ccbd585a152053e552ed18</anchor>
      <arglist>(exp_state_t *exp_param)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_exp</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>ad493be4d8ecd9a7a893225cbcf29f533</anchor>
      <arglist>(exp_state_t *parameter, input_t input)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_initialise</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a30620978a602b7a044f6aaa5880e9341</anchor>
      <arglist>(synapse_types_t *state, synapse_types_params_t *params, uint32_t n_steps_per_time_step)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_save_state</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a04321df403d140de964e5c5a152fe436</anchor>
      <arglist>(synapse_types_t *state, synapse_types_params_t *params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a60079a7d7261fb6e7154977cad9341dc</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_alpha_impl.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types__alpha__impl_8h.html</filename>
    <includes id="decay_8h" name="decay.h" local="no" import="no" module="no" objc="no">neuron/decay.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" import="no" module="no" objc="no">synapse_types.h</includes>
    <class kind="struct">alpha_params_t</class>
    <class kind="struct">synapse_types_params_t</class>
    <class kind="struct">alpha_state_t</class>
    <class kind="struct">synapse_types_t</class>
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
      <anchor>a687a789180879b2c8fe40c120cda5bb1</anchor>
      <arglist>(alpha_state_t *a_params)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>add_input_alpha</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>ad6ed5acc2d19cea1f300ca637d82716a</anchor>
      <arglist>(alpha_state_t *a_params, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a60079a7d7261fb6e7154977cad9341dc</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_delta_impl.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types__delta__impl_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" import="no" module="no" objc="no">synapse_types.h</includes>
    <class kind="struct">synapse_types_params_t</class>
    <class kind="struct">synapse_types_t</class>
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
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a60079a7d7261fb6e7154977cad9341dc</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__delta__impl_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_dual_excitatory_exponential_impl.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types__dual__excitatory__exponential__impl_8h.html</filename>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" import="no" module="no" objc="no">synapse_types.h</includes>
    <includes id="exp__synapse__utils_8h" name="exp_synapse_utils.h" local="yes" import="no" module="no" objc="no">exp_synapse_utils.h</includes>
    <class kind="struct">synapse_types_params_t</class>
    <class kind="struct">synapse_types_t</class>
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
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a60079a7d7261fb6e7154977cad9341dc</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__dual__excitatory__exponential__impl_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_exponential_impl.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types__exponential__impl_8h.html</filename>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" import="no" module="no" objc="no">synapse_types.h</includes>
    <includes id="exp__synapse__utils_8h" name="exp_synapse_utils.h" local="yes" import="no" module="no" objc="no">exp_synapse_utils.h</includes>
    <class kind="struct">synapse_types_params_t</class>
    <class kind="struct">synapse_types_t</class>
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
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a60079a7d7261fb6e7154977cad9341dc</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameters, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__exponential__impl_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_types_semd_impl.h</name>
    <path>src/neuron/synapse_types/</path>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <includes id="synapse__types_8h" name="synapse_types.h" local="yes" import="no" module="no" objc="no">synapse_types.h</includes>
    <includes id="exp__synapse__utils_8h" name="exp_synapse_utils.h" local="yes" import="no" module="no" objc="no">exp_synapse_utils.h</includes>
    <class kind="struct">synapse_types_params_t</class>
    <class kind="struct">synapse_types_t</class>
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
      <name>synapse_types_shape_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>adbe3014909741294cc935642b318df74</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_add_neuron_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a7b40e391b3478e22e6d301eb93e4628f</anchor>
      <arglist>(index_t synapse_type_index, synapse_types_t *parameter, input_t input)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_excitatory_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a1b5bdabe85eb9cad7f78a3bbd5b0f65c</anchor>
      <arglist>(input_t *excitatory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static input_t *</type>
      <name>synapse_types_get_inhibitory_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ae7cdc2c03685f1952eb6f9a1baaa7cb2</anchor>
      <arglist>(input_t *inhibitory_response, synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>synapse_types_get_type_char</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a0724ea81b7a045c34872529ae03d9553</anchor>
      <arglist>(index_t synapse_type_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_input</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a7b7cb2cf40fadcfa990bc69cc8986640</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>synapse_types_print_parameters</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ac952ce9bf740864faedaf4a2c146ca7c</anchor>
      <arglist>(synapse_types_t *parameters)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapses.c</name>
    <path>src/neuron/</path>
    <filename>synapses_8c.html</filename>
    <includes id="synapses_8h" name="synapses.h" local="yes" import="no" module="no" objc="no">synapses.h</includes>
    <includes id="spike__processing_8h" name="spike_processing.h" local="yes" import="no" module="no" objc="no">spike_processing.h</includes>
    <includes id="neuron_8h" name="neuron.h" local="yes" import="no" module="no" objc="no">neuron.h</includes>
    <includes id="synapse__dynamics_8h" name="synapse_dynamics.h" local="yes" import="no" module="no" objc="no">plasticity/synapse_dynamics.h</includes>
    <class kind="struct">synapse_params</class>
    <member kind="function" static="yes">
      <type>static const char *</type>
      <name>get_type_char</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a1a333d14cf1e2ac31a3d3d8bee59dedd</anchor>
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
      <type>static bool</type>
      <name>process_fixed_synapses</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a2432de7c3330e43bd5979f60adc456d0</anchor>
      <arglist>(synapse_row_fixed_part_t *fixed_region, uint32_t time, uint32_t colour_delay)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_initialise</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ab503830b173c644185753159821dbc61</anchor>
      <arglist>(address_t synapse_params_address, uint32_t *n_neurons_out, uint32_t *n_synapse_types_out, weight_t **ring_buffers_out, uint32_t **ring_buffer_to_input_buffer_left_shifts, bool *clear_input_buffers_of_late_packets_init, uint32_t *incoming_spike_buffer_size)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_flush_ring_buffers</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a0eaaa63c7f863ceeb29c428cc67416fe</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_process_synaptic_row</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>adabc60315fbcf7e2da81a0e556d9956f</anchor>
      <arglist>(uint32_t time, uint32_t spike_colour, uint32_t colour_mask, synaptic_row_t row, bool *write_back)</arglist>
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
      <name>synapses_resume</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a96d59593a4844dc703e540f408d22321</anchor>
      <arglist>(timer_t time)</arglist>
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
      <type>static uint32_t</type>
      <name>ring_buffer_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>acdc93525768ee5da66223113c456855f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t *</type>
      <name>ring_buffer_to_input_left_shifts</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ade696d20461dc712b7daafcbcad6ba4b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_index_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ac3299a10c6a78f6e4f37246ab79a0736</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a84db6c41c7cf03558016d477d8df4d37</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>af20079aa1e3c31a3efd344176025ce0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>af786c2a0c6f40c688029991d5b9711a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_delay_bits</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ab03dd903d4fed6afbcd9648d49beb9ae</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_delay_mask</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a2ef4427415ac67eb603a14ca1bb86f83</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapses_saturation_count</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a8b7881a6d9caca38f2050656c652cf26</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>skipped_synapses</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>af61f61aa805ba87019bb5f3f8e44bf0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>late_spikes</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>acd1bff16aec3ed124894cc931af73cda</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_late_spike</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a00a6393e4b2d3b0e80f886244476c8ca</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_neurons_peak</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>a6b1b7d48e24674f12efcb5a84266f969</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>synapse_delay_mask_shifted</name>
      <anchorfile>synapses_8c.html</anchorfile>
      <anchor>ac8536be403f204fda0c5af4f9ff6fc35</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapses.h</name>
    <path>src/neuron/</path>
    <filename>synapses_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="synapse__row_8h" name="synapse_row.h" local="yes" import="no" module="no" objc="no">synapse_row.h</includes>
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
      <anchor>ab86f19d1020a1bcb82decd7fa71e4075</anchor>
      <arglist>(address_t synapse_params_address, uint32_t *n_neurons, uint32_t *n_synapse_types, weight_t **ring_buffers, uint32_t **ring_buffer_to_input_buffer_left_shifts, bool *clear_input_buffers_of_late_packets_init, uint32_t *incoming_spike_buffer_size)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>synapses_process_synaptic_row</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>adabc60315fbcf7e2da81a0e556d9956f</anchor>
      <arglist>(uint32_t time, uint32_t spike_colour, uint32_t colour_mask, synaptic_row_t row, bool *write_back)</arglist>
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
      <name>synapses_resume</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a96d59593a4844dc703e540f408d22321</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>synapses_flush_ring_buffers</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a0eaaa63c7f863ceeb29c428cc67416fe</anchor>
      <arglist>(timer_t time)</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_index_bits</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a4cb72a09cb7c84f5c82c07d17bcb0516</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_index_mask</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>ac3299a10c6a78f6e4f37246ab79a0736</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a840b87d6e981394dff1224fc0b8cd9c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_mask</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a84db6c41c7cf03558016d477d8df4d37</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>af20079aa1e3c31a3efd344176025ce0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_mask</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>af786c2a0c6f40c688029991d5b9711a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_delay_bits</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>ab03dd903d4fed6afbcd9648d49beb9ae</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_delay_mask</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a2ef4427415ac67eb603a14ca1bb86f83</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapses_saturation_count</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a8b7881a6d9caca38f2050656c652cf26</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>skipped_synapses</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>af61f61aa805ba87019bb5f3f8e44bf0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>late_spikes</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>acd1bff16aec3ed124894cc931af73cda</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_late_spike</name>
      <anchorfile>synapses_8h.html</anchorfile>
      <anchor>a00a6393e4b2d3b0e80f886244476c8ca</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>threshold_type.h</name>
    <path>src/neuron/threshold_types/</path>
    <filename>threshold__type_8h.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>threshold_type_initialise</name>
      <anchorfile>threshold__type_8h.html</anchorfile>
      <anchor>a0ccf2c0ff1feb59d7843d6102a4bdfdb</anchor>
      <arglist>(threshold_type_t *state, threshold_type_params_t *params, uint32_t n_steps_per_timestep)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>threshold_type_save_state</name>
      <anchorfile>threshold__type_8h.html</anchorfile>
      <anchor>a230a810f6d449075f7fc416195d4967f</anchor>
      <arglist>(threshold_type_t *state, threshold_type_params_t *params)</arglist>
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
    <name>threshold_type_fixed_prob.h</name>
    <path>src/neuron/threshold_types/</path>
    <filename>threshold__type__fixed__prob_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" import="no" module="no" objc="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_params_t</class>
    <class kind="struct">threshold_type_t</class>
  </compound>
  <compound kind="file">
    <name>threshold_type_maass_stochastic.h</name>
    <path>src/neuron/threshold_types/</path>
    <filename>threshold__type__maass__stochastic_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" import="no" module="no" objc="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_params_t</class>
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
    <path>src/neuron/threshold_types/</path>
    <filename>threshold__type__none_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" import="no" module="no" objc="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_params_t</class>
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
    <path>src/neuron/threshold_types/</path>
    <filename>threshold__type__static_8h.html</filename>
    <includes id="threshold__type_8h" name="threshold_type.h" local="yes" import="no" module="no" objc="no">threshold_type.h</includes>
    <class kind="struct">threshold_type_params_t</class>
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
    <path>src/robot_motor_control/</path>
    <filename>robot__motor__control_8c.html</filename>
    <includes id="neuron-typedefs_8h" name="neuron-typedefs.h" local="no" import="no" module="no" objc="no">common/neuron-typedefs.h</includes>
    <includes id="in__spikes_8h" name="in_spikes.h" local="no" import="no" module="no" objc="no">common/in_spikes.h</includes>
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
    <path>src/spike_source/poisson/</path>
    <filename>spike__source__poisson_8c.html</filename>
    <includes id="maths-util_8h" name="maths-util.h" local="no" import="no" module="no" objc="no">common/maths-util.h</includes>
    <includes id="spike__source_2poisson_2profile__tags_8h" name="profile_tags.h" local="yes" import="no" module="no" objc="no">profile_tags.h</includes>
    <class kind="struct">spike_source_t</class>
    <class kind="struct">timed_out_spikes</class>
    <class kind="struct">rng_seed_t</class>
    <class kind="struct">global_parameters</class>
    <class kind="struct">poisson_extension_provenance</class>
    <class kind="struct">source_info</class>
    <class kind="struct">source_expand_details</class>
    <class kind="struct">source_expand_region</class>
    <class kind="struct">sdram_config</class>
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
      <name>SDRAM_PARAMS_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a83adee9297ce4e0afe12a39cc55f4562</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXPANDER_REGION</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b9edddb3735d131c67e9e824f07c402a719368d00e2ee9a5b0e27a360ea05be4</anchor>
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
      <type>static uint32_t</type>
      <name>rng</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a62b426a3cc403e96d3f3c71761cf797d</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>n_spikes_poisson_fast</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a8c3e0a714592b78c4c9677d663ae5868</anchor>
      <arglist>(UFRACT exp_minus_lambda)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static REAL</type>
      <name>n_steps_until_next</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a45470e19eabdcc8098607930b8aac481</anchor>
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
    <member kind="function">
      <type>void</type>
      <name>set_spike_source_rate</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a92c02fc6489d4fae08305a7d36212cf9</anchor>
      <arglist>(uint32_t sub_id, UREAL rate)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>store_provenance_data</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6a6f18428eca2d03be2d82834e642876</anchor>
      <arglist>(address_t provenance_region)</arglist>
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
      <anchor>a535ce144ca7eade51b6277f40d09136f</anchor>
      <arglist>(source_info *sdram_sources, bool rate_changed, uint32_t next_time)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>initialise_recording</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a25d26d2a2c3ec75e4013c7a5e42bc5a7</anchor>
      <arglist>(data_specification_metadata_t *ds_regions)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>expand_spike_recording_buffer</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a09166600548501c6befb79b410cdc98a</anchor>
      <arglist>(uint32_t n_spikes)</arglist>
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
      <anchor>ad84270695d282c5f3ed37d17b3a68d8e</anchor>
      <arglist>(index_t s_id, spike_source_t *source)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>process_slow_source</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a0133a2417f76bb17221381ed2a1e8be3</anchor>
      <arglist>(index_t s_id, spike_source_t *source)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>timer_callback</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab3ba3db2e11b1db9fd9d1986558eee30</anchor>
      <arglist>(uint timer_count, uint unused)</arglist>
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
    <member kind="variable" static="yes">
      <type>static uint32_t *</type>
      <name>keys</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a803a94ccf2c3fa0146b8c2316fdb850a</anchor>
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
    <member kind="variable" static="yes">
      <type>static struct sdram_config *</type>
      <name>sdram_inputs</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a8bb39ab6e8cf0cf0547ca94315c69ba6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint16_t *</type>
      <name>input_this_timestep</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a148ad514a3ea3af1eae2a8a354f242c2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static UREAL</type>
      <name>ts_per_second</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a3d336819c22c6a3bcda7ba321da3741b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static circular_buffer</type>
      <name>rate_change_buffer</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1725d9f0f0d4af892f22a0181e4fdeac</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>colour</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a5bdac4fec3cf570ebe861aea93346316</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>colour_mask</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a4aa662177b306e9085f7ef20b3a6a2c1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static uint32_t</type>
      <name>n_saturations</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab1ae1a332cf8e1862c7a299b9c9a03bf</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>bit_field_expander.h</name>
    <path>src/synapse_expander/</path>
    <filename>bit__field__expander_8h.html</filename>
    <includes id="synapse__row_8h" name="synapse_row.h" local="no" import="no" module="no" objc="no">neuron/synapse_row.h</includes>
    <includes id="population__table_8h" name="population_table.h" local="no" import="no" module="no" objc="no">neuron/population_table/population_table.h</includes>
    <includes id="sp__structs_8h" name="sp_structs.h" local="no" import="no" module="no" objc="no">neuron/structural_plasticity/synaptogenesis/sp_structs.h</includes>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>do_sdram_read_and_test</name>
      <anchorfile>bit__field__expander_8h.html</anchorfile>
      <anchor>aedbb9078114fc3e4f94a7e6c4ca3c5ae</anchor>
      <arglist>(synaptic_row_t row_data, pop_table_lookup_result_t *result)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>determine_redundancy</name>
      <anchorfile>bit__field__expander_8h.html</anchorfile>
      <anchor>a15cfb9de720808f7005d7d93f426c162</anchor>
      <arglist>(filter_region_t *bitfield_filters)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>generate_bit_field</name>
      <anchorfile>bit__field__expander_8h.html</anchorfile>
      <anchor>ac4477b4a6faf287e216d3a2ba19f91ca</anchor>
      <arglist>(filter_region_t *bitfield_filters, uint32_t *n_atom_data, void *synaptic_matrix, void *structural_matrix, pre_pop_info_table_t *pre_info, synaptic_row_t row_data)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>do_bitfield_generation</name>
      <anchorfile>bit__field__expander_8h.html</anchorfile>
      <anchor>a9fb8dd78e38e33e88fa72cc981744d2a</anchor>
      <arglist>(uint32_t *n_atom_data_sdram, void *master_pop, void *synaptic_matrix, void *bitfield_filters, void *structural_matrix)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>common_kernel.c</name>
    <path>src/synapse_expander/</path>
    <filename>common__kernel_8c.html</filename>
    <includes id="common__kernel_8h" name="common_kernel.h" local="yes" import="no" module="no" objc="no">common_kernel.h</includes>
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
    <path>src/synapse_expander/</path>
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
    <path>src/synapse_expander/</path>
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
    <path>src/synapse_expander/</path>
    <filename>connection__generator_8c.html</filename>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" import="no" module="no" objc="no">connection_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" import="no" module="no" objc="no">generator_types.h</includes>
    <includes id="connection__generator__one__to__one_8h" name="connection_generator_one_to_one.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_one_to_one.h</includes>
    <includes id="connection__generator__all__to__all_8h" name="connection_generator_all_to_all.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_all_to_all.h</includes>
    <includes id="connection__generator__fixed__prob_8h" name="connection_generator_fixed_prob.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_fixed_prob.h</includes>
    <includes id="connection__generator__fixed__total_8h" name="connection_generator_fixed_total.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_fixed_total.h</includes>
    <includes id="connection__generator__fixed__pre_8h" name="connection_generator_fixed_pre.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_fixed_pre.h</includes>
    <includes id="connection__generator__fixed__post_8h" name="connection_generator_fixed_post.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_fixed_post.h</includes>
    <includes id="connection__generator__kernel_8h" name="connection_generator_kernel.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_kernel.h</includes>
    <includes id="connection__generator__all__but__me_8h" name="connection_generator_all_but_me.h" local="yes" import="no" module="no" objc="no">connection_generators/connection_generator_all_but_me.h</includes>
    <class kind="struct">connection_generator_info</class>
    <class kind="struct">connection_generator</class>
    <member kind="enumvalue">
      <name>ONE_TO_ONE</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fceadaccc17f840cc67d0e9c1a9a331b2fb4</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ALL_TO_ALL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fcea403e4025d2925f132293a50eae7381fe</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_PROBABILITY</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fcea8f6a6db47b5476cf11f24317f14ee4a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_TOTAL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fcea8338dcf5840ce1a01a4c26d9c49dc560</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_PRE</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fceaa667dfec30c43a0320c7bd76b99bd4c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>FIXED_POST</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fceaa130e7b038fc0ede3b0203931063b116</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>KERNEL</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fcea53c6e691e7db9eceefc0fb37cb724cd2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>ALL_BUT_ME</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fcea37abc5f972bd9d81bd02f1ede4200e1e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_CONNECTION_GENERATORS</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aaf105ae5beaca1dee30ae54530691fceab1144285d7382feeb4687af0263e2467</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>connection_generator_t</type>
      <name>connection_generator_init</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aa5d2850a976b1db33c19af00ad9fcc67</anchor>
      <arglist>(uint32_t hash, void **in_region)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>connection_generator_generate</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>aae17e4a6bdf077f36b078033db1c7fbe</anchor>
      <arglist>(connection_generator_t generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
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
    <path>src/synapse_expander/</path>
    <filename>connection__generator_8h.html</filename>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" import="no" module="no" objc="no">param_generator.h</includes>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" import="no" module="no" objc="no">matrix_generator.h</includes>
    <member kind="function">
      <type>connection_generator_t</type>
      <name>connection_generator_init</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>a48471e82d8fe492b0f961147c69477ad</anchor>
      <arglist>(uint32_t hash, void **region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>connection_generator_free</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>ab9b132e35b3d39240d34e7f225193910</anchor>
      <arglist>(connection_generator_t generator)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>connection_generator_generate</name>
      <anchorfile>connection__generator_8h.html</anchorfile>
      <anchor>aae17e4a6bdf077f36b078033db1c7fbe</anchor>
      <arglist>(connection_generator_t generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_all_but_me.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__all__but__me_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">all_but_me_conf</class>
    <class kind="struct">all_but_me</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_all_but_me_initialise</name>
      <anchorfile>connection__generator__all__but__me_8h.html</anchorfile>
      <anchor>a2aa78b833aead77694d27666289a119b</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_all_but_me_free</name>
      <anchorfile>connection__generator__all__but__me_8h.html</anchorfile>
      <anchor>a1a40c2d7750a8a0088cfd941edf93e29</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>get_weight</name>
      <anchorfile>connection__generator__all__but__me_8h.html</anchorfile>
      <anchor>a92f901f11db3fa84feb3cd401e4ca672</anchor>
      <arglist>(struct all_but_me *obj, param_generator_t weight_generator, uint32_t pre_value, uint32_t post_value)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_all_but_me_generate</name>
      <anchorfile>connection__generator__all__but__me_8h.html</anchorfile>
      <anchor>a9807e38c00ed1f42fe51fd652e0fd338</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_all_to_all.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__all__to__all_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">all_to_all</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_all_to_all_initialise</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a4b108e7a6f036749f5e95c75c42ad5ec</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_all_to_all_free</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>a71eb137d1e03e170895b6bf705bcd0bd</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_all_to_all_generate</name>
      <anchorfile>connection__generator__all__to__all_8h.html</anchorfile>
      <anchor>af13222b82326b2caa582ee2b216252de</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_post.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__post_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <class kind="struct">fixed_post_params</class>
    <class kind="struct">fixed_post</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_post_initialise</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a693239adbef288dda13b0c6530e47c56</anchor>
      <arglist>(void **region)</arglist>
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
      <anchor>a379e0e6995c258b9d2944d38f5bc3f6e</anchor>
      <arglist>(rng_t *rng, uint32_t range)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_fixed_post_generate</name>
      <anchorfile>connection__generator__fixed__post_8h.html</anchorfile>
      <anchor>a7d6fda536e854ee9bab7178fd773b5a9</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_pre.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <class kind="struct">fixed_pre_params</class>
    <class kind="struct">fixed_pre</class>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>pre_random_in_range</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>aa37d4d25b55098b93af4cf67d51a6911</anchor>
      <arglist>(rng_t *rng, uint32_t range)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_pre_initialise</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a6f42d103a8e2a6767ff3acefca67076f</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>connection_generator_fixed_pre_free</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>ac7bbf4bf4f70b6455cb935e57165a614</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>connection_generator_fixed_pre_generate</name>
      <anchorfile>connection__generator__fixed__pre_8h.html</anchorfile>
      <anchor>a7451194e2c09026732c5d82654c8120c</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_prob.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__prob_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">fixed_prob_params</class>
    <class kind="struct">fixed_prob</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_prob_initialise</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>a2fc35e6abb5092061cf619615b65e385</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_fixed_prob_free</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>ad5ab082c89ff3e5317a09aa7f67a6442</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_fixed_prob_generate</name>
      <anchorfile>connection__generator__fixed__prob_8h.html</anchorfile>
      <anchor>ac8b2f5a508831466425f0f0967a30604</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_fixed_total.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__fixed__total_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">fixed_total_params</class>
    <class kind="struct">fixed_total</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_fixed_total_initialise</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a511965266bcd412ca17e61aa8651b71e</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_fixed_total_free</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a0d3e8f5ac6f3487cc51cf868f75e7619</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_fixed_total_generate</name>
      <anchorfile>connection__generator__fixed__total_8h.html</anchorfile>
      <anchor>a5326514456754b8f06dfff55a3d4ee7a</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_kernel.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__kernel_8h.html</filename>
    <includes id="common__kernel_8h" name="common_kernel.h" local="no" import="no" module="no" objc="no">synapse_expander/common_kernel.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="no" import="no" module="no" objc="no">synapse_expander/common_mem.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">kernel</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_kernel_initialise</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a0f9f9790bda6198acbb71dcd1dfb64fe</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_kernel_free</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a0e3d6a7e01f6bcfe0c5f9063e879bff2</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_kernel_generate</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a9d2040bb7df48fbe84c9ce51256964a3</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>connection_generator_one_to_one.h</name>
    <path>src/synapse_expander/connection_generators/</path>
    <filename>connection__generator__one__to__one_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>connection_generator_one_to_one_initialise</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>aebf476a54cd4676d243dfc25c6d0b9ba</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>connection_generator_one_to_one_free</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>a519a2706ae01863c6124c8dc78a6a8a7</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>connection_generator_one_to_one_generate</name>
      <anchorfile>connection__generator__one__to__one_8h.html</anchorfile>
      <anchor>a0995920e464679529f2a804431341768</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>generator_types.h</name>
    <path>src/synapse_expander/</path>
    <filename>generator__types_8h.html</filename>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" import="no" module="no" objc="no">param_generator.h</includes>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" import="no" module="no" objc="no">matrix_generator.h</includes>
    <member kind="typedef">
      <type>uint32_t</type>
      <name>generator_hash_t</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a55f8d20fc9350939e3fa6a85d8aed90c</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>void *()</type>
      <name>initialize_param_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>af81c9a4b29b65e35026b5f01847ba9b4</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="typedef">
      <type>void *()</type>
      <name>initialize_connector_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a2dcb0fed4f9ddff8fc78d06b3fe93a80</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="typedef">
      <type>void *()</type>
      <name>initialize_matrix_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a3570e47f1d4c9abba08df76f4aaa87e9</anchor>
      <arglist>(void **region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="typedef">
      <type>void()</type>
      <name>free_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a6b16387baa51e7bff16f0e21220c254e</anchor>
      <arglist>(void *data)</arglist>
    </member>
    <member kind="typedef">
      <type>accum()</type>
      <name>generate_param_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>aeb13a16410f550a8620d9db733b00114</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="typedef">
      <type>bool()</type>
      <name>write_synapse_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a2ddfc8a6851657caf368b43e958e7cdf</anchor>
      <arglist>(void *generator, uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay, unsigned long accum weight_scale)</arglist>
    </member>
    <member kind="typedef">
      <type>bool()</type>
      <name>generate_connection_func</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>ae7498b5ac57ed8c5279e034819ae4c3f</anchor>
      <arglist>(void *generator, uint32_t pre_lo, uint32_t pre_hi, uint32_t post_lo, uint32_t post_hi, uint32_t post_index, uint32_t post_slice_start, uint32_t post_slice_count, unsigned long accum weight_scale, accum timestep_per_delay, param_generator_t weight_generator, param_generator_t delay_generator, matrix_generator_t matrix_generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>rescale_delay</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>abe727a061d0165e4205bb2764711e760</anchor>
      <arglist>(accum delay, accum timestep_per_delay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>rescale_weight</name>
      <anchorfile>generator__types_8h.html</anchorfile>
      <anchor>a5ee0662d7b826e8ba7abfa68bbe6a327</anchor>
      <arglist>(accum weight, unsigned long accum weight_scale)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator.c</name>
    <path>src/synapse_expander/</path>
    <filename>matrix__generator_8c.html</filename>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" import="no" module="no" objc="no">matrix_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" import="no" module="no" objc="no">generator_types.h</includes>
    <includes id="matrix__generator__static_8h" name="matrix_generator_static.h" local="yes" import="no" module="no" objc="no">matrix_generators/matrix_generator_static.h</includes>
    <includes id="matrix__generator__stdp_8h" name="matrix_generator_stdp.h" local="yes" import="no" module="no" objc="no">matrix_generators/matrix_generator_stdp.h</includes>
    <includes id="matrix__generator__neuromodulation_8h" name="matrix_generator_neuromodulation.h" local="yes" import="no" module="no" objc="no">matrix_generators/matrix_generator_neuromodulation.h</includes>
    <includes id="matrix__generator__weight__changer_8h" name="matrix_generator_weight_changer.h" local="yes" import="no" module="no" objc="no">matrix_generators/matrix_generator_weight_changer.h</includes>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" import="no" module="no" objc="no">delay_extension/delay_extension.h</includes>
    <class kind="struct">matrix_generator_info</class>
    <class kind="struct">matrix_generator</class>
    <member kind="enumvalue">
      <name>STATIC_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a80155586fa275b28773c9b203f52cabaaf14f18f5ed2665f8cb095c1363fc9848</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>PLASTIC_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a80155586fa275b28773c9b203f52cabaa08b27fbab7a770bae071d9defb278782</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NEUROMODULATION_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a80155586fa275b28773c9b203f52cabaa6b120ed291bedd7072f69611ed7f1732</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>WEIGHT_CHANGER_MATRIX_GENERATOR</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a80155586fa275b28773c9b203f52cabaa391031f51ef8b5851d8fb3a6ef0f4b1b</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_MATRIX_GENERATORS</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a80155586fa275b28773c9b203f52cabaaba9a03e4fd023b2837469ea1ff6225a3</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>matrix_generator_t</type>
      <name>matrix_generator_init</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a1251737c3f53736fac48f2f91f1b082e</anchor>
      <arglist>(uint32_t hash, void **in_region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_free</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>aafbab40316b9861d41999287c65d1dbe</anchor>
      <arglist>(matrix_generator_t generator)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>matrix_generator_write_synapse</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a7d0ab0ac823dba9d0d1bfaa5304d4fda</anchor>
      <arglist>(matrix_generator_t generator, uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay, unsigned long accum weight_scale)</arglist>
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
    <path>src/synapse_expander/</path>
    <filename>matrix__generator_8h.html</filename>
    <member kind="function">
      <type>matrix_generator_t</type>
      <name>matrix_generator_init</name>
      <anchorfile>matrix__generator_8h.html</anchorfile>
      <anchor>a8fbcc0eb851d4f4ba5952ba9e3459e93</anchor>
      <arglist>(uint32_t hash, void **region, void *synaptic_matrix)</arglist>
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
      <name>matrix_generator_write_synapse</name>
      <anchorfile>matrix__generator_8h.html</anchorfile>
      <anchor>a7d0ab0ac823dba9d0d1bfaa5304d4fda</anchor>
      <arglist>(matrix_generator_t generator, uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay, unsigned long accum weight_scale)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_common.h</name>
    <path>src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__common_8h.html</filename>
    <class kind="struct">delay_value</class>
    <member kind="define">
      <type>#define</type>
      <name>N_HEADER_WORDS</name>
      <anchorfile>matrix__generator__common_8h.html</anchorfile>
      <anchor>a04acf43728100eca08ffab028792301a</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static struct delay_value</type>
      <name>get_delay</name>
      <anchorfile>matrix__generator__common_8h.html</anchorfile>
      <anchor>a70d02afe8081b6ed99856fe4594e88e8</anchor>
      <arglist>(uint16_t delay_value, uint32_t max_stage, uint32_t max_delay_per_stage)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>get_row</name>
      <anchorfile>matrix__generator__common_8h.html</anchorfile>
      <anchor>ae4c39a14584912fa86c805ebcdfec177</anchor>
      <arglist>(uint32_t *synaptic_matrix, uint32_t max_row_n_words, uint32_t pre_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>get_delay_row</name>
      <anchorfile>matrix__generator__common_8h.html</anchorfile>
      <anchor>aa78206950a7ea5913dd02cb1b2d27c1a</anchor>
      <arglist>(uint32_t *delayed_synaptic_matrix, uint32_t max_delayed_row_n_words, uint32_t pre_index, uint32_t delay_stage, uint32_t n_pre_neurons_per_core, uint32_t max_delay_stage, uint32_t n_pre_neurons)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_neuromodulation.h</name>
    <path>src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__neuromodulation_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" import="no" module="no" objc="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" import="no" module="no" objc="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">matrix_generator_neuromodulation</class>
    <class kind="struct">row_nm_plastic_t</class>
    <class kind="struct">row_nm_fixed_t</class>
    <class kind="union">matrix_generator_neuromodulation.__unnamed19__</class>
    <member kind="function" static="yes">
      <type>static row_nm_plastic_t *</type>
      <name>get_nm_row</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a1a29f0db40c53c9eb7514bc9b543f2a9</anchor>
      <arglist>(uint32_t *synaptic_matrix, uint32_t max_row_n_words, uint32_t pre_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static row_nm_fixed_t *</type>
      <name>get_nm_fixed_row</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a3c46723fedbc28bed3058596ce6417f0</anchor>
      <arglist>(row_nm_plastic_t *plastic_row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_nm_rows</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>aac7b4d7aaf8b502f118972ae9bdb0bef</anchor>
      <arglist>(uint32_t *matrix, uint32_t n_rows, uint32_t max_row_n_words, uint32_t is_reward, uint32_t synapse_type)</arglist>
    </member>
    <member kind="function">
      <type>void *</type>
      <name>matrix_generator_neuromodulation_initialize</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>aabd3bff0ee801e41e21e39601232b88e</anchor>
      <arglist>(void **region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_neuromodulation_free</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>ab99540990f72253026bd7c4ee437e444</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_static.h</name>
    <path>src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__static_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" import="no" module="no" objc="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" import="no" module="no" objc="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">static_row_t</class>
    <class kind="struct">matrix_genetator_static_data_t</class>
    <class kind="union">matrix_genetator_static_data_t.__unnamed21__</class>
    <class kind="union">matrix_genetator_static_data_t.__unnamed23__</class>
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
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_rows</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>ad8a76e9758256ce53a6f257964452086</anchor>
      <arglist>(uint32_t *matrix, uint32_t n_rows, uint32_t max_row_n_words)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>build_static_word</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a9668b8739759b825c0adc78440bfa352</anchor>
      <arglist>(uint16_t weight, uint16_t delay, uint32_t type, uint16_t post_index, uint32_t synapse_type_bits, uint32_t synapse_index_bits, uint32_t delay_bits)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>matrix_generator_static_initialize</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a9b1343f78127a9bdfd51ae87f2b4f589</anchor>
      <arglist>(void **region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>matrix_generator_static_free</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a21c6ce388b821caaa1268c3d6abb9ef1</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>matrix_generator_static_write_synapse</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a158569634b57155a6c5b62e4cb782979</anchor>
      <arglist>(void *generator, uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay, unsigned long accum weight_scale)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_stdp.h</name>
    <path>src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__stdp_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" import="no" module="no" objc="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" import="no" module="no" objc="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">row_plastic_t</class>
    <class kind="struct">row_fixed_t</class>
    <class kind="struct">matrix_generator_stdp_data_t</class>
    <class kind="union">matrix_generator_stdp_data_t.__unnamed25__</class>
    <class kind="union">matrix_generator_stdp_data_t.__unnamed27__</class>
    <member kind="function" static="yes">
      <type>static uint32_t</type>
      <name>plastic_half_words</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a3a5ed9ae80176b92497373cd16a53989</anchor>
      <arglist>(uint32_t n_half_words_per_pp_header, uint32_t n_half_words_per_pp_synapse, uint32_t max_row_n_synapses)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static row_fixed_t *</type>
      <name>get_stdp_fixed_row</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a97c90fc0e4a1cf3399c32a8421380e9a</anchor>
      <arglist>(row_plastic_t *plastic_row, uint32_t n_half_words_per_pp_header, uint32_t n_half_words_per_pp_synapse, uint32_t max_row_n_synapses)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_stdp_rows</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>abf6239622dfc48b7cdb9415ac2476a33</anchor>
      <arglist>(uint32_t *matrix, uint32_t n_rows, uint32_t n_half_words_per_pp_header, uint32_t n_half_words_per_pp_synapse, uint32_t max_row_n_synapses, uint32_t max_row_n_words, uint32_t first_header_word_is_row_index, uint32_t row_offset)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static uint16_t</type>
      <name>build_fixed_plastic_half_word</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ad136b625e3f52e67d888a50058e43a16</anchor>
      <arglist>(uint16_t delay, uint32_t type, uint32_t post_index, uint32_t synapse_type_bits, uint32_t synapse_index_bits, uint32_t delay_bits)</arglist>
    </member>
    <member kind="function">
      <type>void *</type>
      <name>matrix_generator_stdp_initialize</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a144a74fd40261e36cef9ba032b6674e1</anchor>
      <arglist>(void **region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_stdp_free</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aa0ccbf6127b7bd9ba00efc3ba17373e9</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>matrix_generator_stdp_write_synapse</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aa7dc79c13959aa923b5193e825048565</anchor>
      <arglist>(void *generator, uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay, unsigned long accum weight_scale)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>matrix_generator_weight_changer.h</name>
    <path>src/synapse_expander/matrix_generators/</path>
    <filename>matrix__generator__weight__changer_8h.html</filename>
    <includes id="delay__extension_8h" name="delay_extension.h" local="no" import="no" module="no" objc="no">delay_extension/delay_extension.h</includes>
    <includes id="matrix__generator__common_8h" name="matrix_generator_common.h" local="yes" import="no" module="no" objc="no">matrix_generator_common.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">matrix_generator_weight_changer</class>
    <class kind="struct">row_changer_plastic_t</class>
    <class kind="struct">row_changer_fixed_t</class>
    <class kind="union">matrix_generator_weight_changer.__unnamed29__</class>
    <member kind="function" static="yes">
      <type>static row_changer_plastic_t *</type>
      <name>get_changer_row</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a5ac084e6d4089f0bfda689bfdf769968</anchor>
      <arglist>(uint32_t *synaptic_matrix, uint32_t max_row_n_words, uint32_t pre_index)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static row_changer_fixed_t *</type>
      <name>get_changer_fixed_row</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a078340af91c9659c0ef4fc46e4a1a4b0</anchor>
      <arglist>(row_changer_plastic_t *plastic_row)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>setup_changer_rows</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a037cde80ca8f9826d7c7796a52c19498</anchor>
      <arglist>(uint32_t *matrix, uint32_t n_rows, uint32_t max_row_n_words, uint32_t row_offset)</arglist>
    </member>
    <member kind="function">
      <type>void *</type>
      <name>matrix_generator_changer_initialize</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>acca77f2ed6b8c0e3ccf5e42b13693280</anchor>
      <arglist>(void **region, void *synaptic_matrix)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>matrix_generator_changer_free</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a396d5705ee3d6a07d54e23870b8d3602</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>neuron_expander.c</name>
    <path>src/synapse_expander/</path>
    <filename>neuron__expander_8c.html</filename>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" import="no" module="no" objc="no">param_generator.h</includes>
    <includes id="rng_8h" name="rng.h" local="yes" import="no" module="no" objc="no">rng.h</includes>
    <includes id="type__writers_8h" name="type_writers.h" local="yes" import="no" module="no" objc="no">type_writers.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" import="no" module="no" objc="no">common_mem.h</includes>
    <class kind="struct">neuron_param_item_t</class>
    <class kind="struct">neuron_param_t</class>
    <class kind="struct">neuron_params_struct_t</class>
    <class kind="struct">sdram_variable_recording_data_t</class>
    <class kind="struct">sdram_bitfield_recording_data_t</class>
    <class kind="struct">recording_index_t</class>
    <class kind="struct">variable_recording_t</class>
    <class kind="struct">bitfield_recording_t</class>
    <class kind="struct">recording_params_t</class>
    <member kind="define">
      <type>#define</type>
      <name>FLOOR_TO_2</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>a403b173ad583ec922758a7edc380fa3c</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CEIL_TO_2</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>aa2d4795fc5236852254c8bebccde5764</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_struct_builder_region</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>aef4672e3d943cabed294c6a5faa1c674</anchor>
      <arglist>(void **region, void **neuron_params_region, uint32_t n_neurons)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>run_neuron_expander</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>a7aed94e2eb1e4c346934267636aa6008</anchor>
      <arglist>(data_specification_metadata_t *ds_regions, void *params_address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>population_rng</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>aa5d23a2beb618420408ca4853051f042</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>core_rng</name>
      <anchorfile>neuron__expander_8c.html</anchorfile>
      <anchor>a5ca5c820c3873b51d8ca1ad0d35eb075</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator.c</name>
    <path>src/synapse_expander/</path>
    <filename>param__generator_8c.html</filename>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" import="no" module="no" objc="no">param_generator.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="yes" import="no" module="no" objc="no">generator_types.h</includes>
    <includes id="param__generator__constant_8h" name="param_generator_constant.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_constant.h</includes>
    <includes id="param__generator__uniform_8h" name="param_generator_uniform.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_uniform.h</includes>
    <includes id="param__generator__normal_8h" name="param_generator_normal.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_normal.h</includes>
    <includes id="param__generator__normal__clipped_8h" name="param_generator_normal_clipped.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_normal_clipped.h</includes>
    <includes id="param__generator__normal__clipped__to__boundary_8h" name="param_generator_normal_clipped_to_boundary.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_normal_clipped_to_boundary.h</includes>
    <includes id="param__generator__exponential_8h" name="param_generator_exponential.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_exponential.h</includes>
    <includes id="param__generator__exponential__clipped_8h" name="param_generator_exponential_clipped.h" local="yes" import="no" module="no" objc="no">param_generators/param_generator_exponential_clipped.h</includes>
    <class kind="struct">param_generator_info</class>
    <class kind="struct">param_generator</class>
    <member kind="enumvalue">
      <name>CONSTANT</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebba83972670b57415508523b5641bb46116</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>UNIFORM</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebba8f44784d154005a214e0fe94119d28ef</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebba50d1448013c6f17125caee18aa418af7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL_CLIPPED</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebbac40cefd2a096660da3f41d6ee6352889</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>NORMAL_CLIPPED_BOUNDARY</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebbaca06c44d4221f47f9d61534ca1e35752</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXPONENTIAL</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebbaa6055a3a8ab1aed0594419b51d9ec15e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>EXPONENTIAL_CLIPPED</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebbaf2695167689db2a433e28e813f6d88f3</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>N_PARAM_GENERATORS</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a0ed680fdb405e7195d9f14032851eebbab8047ff7dfdb2c76ef1e78a7e6347777</anchor>
      <arglist></arglist>
    </member>
    <member kind="function">
      <type>param_generator_t</type>
      <name>param_generator_init</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>adbbfc064d4b66fdcb5738b2a0852dd21</anchor>
      <arglist>(uint32_t hash, void **in_region)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>param_generator_generate</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>afef726e38862303036b706f63cb5408d</anchor>
      <arglist>(param_generator_t generator)</arglist>
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
    <path>src/synapse_expander/</path>
    <filename>param__generator_8h.html</filename>
    <member kind="function">
      <type>param_generator_t</type>
      <name>param_generator_init</name>
      <anchorfile>param__generator_8h.html</anchorfile>
      <anchor>aa8fc0d4f24db6ca96094f0aed98867cc</anchor>
      <arglist>(uint32_t hash, void **region)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>param_generator_generate</name>
      <anchorfile>param__generator_8h.html</anchorfile>
      <anchor>afef726e38862303036b706f63cb5408d</anchor>
      <arglist>(param_generator_t generator)</arglist>
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
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__constant_8h.html</filename>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_constant</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_constant_initialize</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>a6104ee09a74d6c4a766412ed986d967c</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_constant_free</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>ae74a9c20cfc678e6ddd497a11385af04</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_constant_generate</name>
      <anchorfile>param__generator__constant_8h.html</anchorfile>
      <anchor>a77b1ea38243a82710e7a32d1ff1c1298</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_exponential.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__exponential_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_exponential_params</class>
    <class kind="struct">param_generator_exponential</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_exponential_initialize</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a87ee3b399a3ce5a01937a66d62af5111</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_exponential_free</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a5e6bcf3faf8c177cd11b9aa85f8332ab</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_exponential_generate</name>
      <anchorfile>param__generator__exponential_8h.html</anchorfile>
      <anchor>a0b7052da706984ea9afd03182b04db9e</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_exponential_clipped.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__exponential__clipped_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">param_generator_exponential_clipped_params</class>
    <class kind="struct">param_generator_exponential_clipped</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_REDRAWS</name>
      <anchorfile>param__generator__exponential__clipped_8h.html</anchorfile>
      <anchor>a47fa28c0ff86570b51eb712e1c37a9bd</anchor>
      <arglist></arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_exponential_clipped_initialize</name>
      <anchorfile>param__generator__exponential__clipped_8h.html</anchorfile>
      <anchor>ab8780fa58f53712b58f8a6388ddce6d1</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_exponential_clipped_free</name>
      <anchorfile>param__generator__exponential__clipped_8h.html</anchorfile>
      <anchor>ab8a81a5dc3ed66df57d4ea72b4f737f4</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_exponential_clipped_generate</name>
      <anchorfile>param__generator__exponential__clipped_8h.html</anchorfile>
      <anchor>a5a9bb4416af96291978f81160ab26d3c</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">normal_params</class>
    <class kind="struct">param_generator_normal</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_normal_initialize</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>a2ee856e088ff37c883d80b2b7f8a7ab9</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_free</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>a5da899810d276b0a718b0802fb176783</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_normal_generate</name>
      <anchorfile>param__generator__normal_8h.html</anchorfile>
      <anchor>ab4675e8a38c5ceb893c1bfeb9855d674</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal_clipped.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal__clipped_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
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
      <anchor>adcec4001204f87a9e238f723067c331c</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_free</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>aa9c765cadcfd29badb3aa2b96aa6ace2</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_normal_clipped_generate</name>
      <anchorfile>param__generator__normal__clipped_8h.html</anchorfile>
      <anchor>a2689af6a3a0e75893cb57cbb0f9225a3</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_normal_clipped_to_boundary.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__normal__clipped__to__boundary_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">normal_clipped_boundary_params</class>
    <class kind="struct">param_generator_normal_clipped_boundary</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_normal_clipped_boundary_initialize</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>a0c093e3e508f47df155e5b51cfbcd897</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_normal_clipped_boundary_free</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>a5da6f0676e55afbd36f5a0922c5c33f9</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_normal_clipped_boundary_generate</name>
      <anchorfile>param__generator__normal__clipped__to__boundary_8h.html</anchorfile>
      <anchor>ab66a10e3ada868e5462a6b67c3c81d6d</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>param_generator_uniform.h</name>
    <path>src/synapse_expander/param_generators/</path>
    <filename>param__generator__uniform_8h.html</filename>
    <includes id="rng_8h" name="rng.h" local="no" import="no" module="no" objc="no">synapse_expander/rng.h</includes>
    <includes id="generator__types_8h" name="generator_types.h" local="no" import="no" module="no" objc="no">synapse_expander/generator_types.h</includes>
    <class kind="struct">uniform_params</class>
    <class kind="struct">param_generator_uniform</class>
    <member kind="function" static="yes">
      <type>static void *</type>
      <name>param_generator_uniform_initialize</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>a738047e64cc7e8589b3d4bb65bb23eef</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static void</type>
      <name>param_generator_uniform_free</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>a445a600b3abdfaa44355db5151482756</anchor>
      <arglist>(void *generator)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static accum</type>
      <name>param_generator_uniform_generate</name>
      <anchorfile>param__generator__uniform_8h.html</anchorfile>
      <anchor>a2b29e827b33797b652c59eb606a042b5</anchor>
      <arglist>(void *generator)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>rng.c</name>
    <path>src/synapse_expander/</path>
    <filename>rng_8c.html</filename>
    <includes id="rng_8h" name="rng.h" local="yes" import="no" module="no" objc="no">rng.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" import="no" module="no" objc="no">common_mem.h</includes>
    <member kind="function">
      <type>uint32_t</type>
      <name>rng_generator</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>aad3647089384bbdbd3a58476639d7b47</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_exponential</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>a26876180ba17fcab970dcf37b27f7e8e</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_normal</name>
      <anchorfile>rng_8c.html</anchorfile>
      <anchor>a5677399580a8c95d1359086be8b7d5c3</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>rng.h</name>
    <path>src/synapse_expander/</path>
    <filename>rng_8h.html</filename>
    <class kind="struct">rng_t</class>
    <member kind="function">
      <type>rng_t *</type>
      <name>rng_init</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>ab418120c63d99f031b5a17d5fd6dcd05</anchor>
      <arglist>(void **region)</arglist>
    </member>
    <member kind="function">
      <type>uint32_t</type>
      <name>rng_generator</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>aad3647089384bbdbd3a58476639d7b47</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_exponential</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a26876180ba17fcab970dcf37b27f7e8e</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="function">
      <type>accum</type>
      <name>rng_normal</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a5677399580a8c95d1359086be8b7d5c3</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>rng_free</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a834d6cf1f8eae1fcc729cc27548d39f8</anchor>
      <arglist>(rng_t *rng)</arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>population_rng</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>aa5d23a2beb618420408ca4853051f042</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>core_rng</name>
      <anchorfile>rng_8h.html</anchorfile>
      <anchor>a5ca5c820c3873b51d8ca1ad0d35eb075</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>synapse_expander.c</name>
    <path>src/synapse_expander/</path>
    <filename>synapse__expander_8c.html</filename>
    <includes id="matrix__generator_8h" name="matrix_generator.h" local="yes" import="no" module="no" objc="no">matrix_generator.h</includes>
    <includes id="connection__generator_8h" name="connection_generator.h" local="yes" import="no" module="no" objc="no">connection_generator.h</includes>
    <includes id="param__generator_8h" name="param_generator.h" local="yes" import="no" module="no" objc="no">param_generator.h</includes>
    <includes id="rng_8h" name="rng.h" local="yes" import="no" module="no" objc="no">rng.h</includes>
    <includes id="common__mem_8h" name="common_mem.h" local="yes" import="no" module="no" objc="no">common_mem.h</includes>
    <includes id="bit__field__expander_8h" name="bit_field_expander.h" local="yes" import="no" module="no" objc="no">bit_field_expander.h</includes>
    <class kind="struct">connection_builder_config_t</class>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>read_connection_builder_region</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>a548180c2ae9037f4c97c68f173aff027</anchor>
      <arglist>(void **region, void *synaptic_matrix, uint32_t post_slice_start, uint32_t post_slice_count, uint32_t post_index, unsigned long accum *weight_scales, accum timestep_per_delay)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static bool</type>
      <name>run_synapse_expander</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>aeb2b0ef5d12497ec1db7032e98249f94</anchor>
      <arglist>(data_specification_metadata_t *ds_regions, void *params_address)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>c_main</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>aa14f4f1d4c84183b7bf7108bf930a23c</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>population_rng</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>aa5d23a2beb618420408ca4853051f042</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rng_t *</type>
      <name>core_rng</name>
      <anchorfile>synapse__expander_8c.html</anchorfile>
      <anchor>a5ca5c820c3873b51d8ca1ad0d35eb075</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>type_writers.h</name>
    <path>src/synapse_expander/</path>
    <filename>type__writers_8h.html</filename>
    <class kind="struct">type_info</class>
  </compound>
  <compound kind="struct">
    <name>ac_source_t</name>
    <filename>current__source__ac_8h.html</filename>
    <anchor>structac__source__t</anchor>
  </compound>
  <compound kind="struct">
    <name>additional_input_params_t</name>
    <filename>additional__input__none__impl_8h.html</filename>
    <anchor>structadditional__input__params__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>tau_ca2</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>ac22854ff32cfd7eff2c437e7cbe3d916</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>i_ca2</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a768961992bddb5df5196cbdcb5d66d19</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>i_alpha</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>acf4f13bc8b7bec63ae92dc94c7c9dde7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>time_step</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>abe999050dbc488cdc08c6a8948366a0e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>additional_input_t</name>
    <filename>additional__input__none__impl_8h.html</filename>
    <anchor>structadditional__input__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>exp_tau_ca2</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a4dda6255b178cc18bef923ca6851f071</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>i_ca2</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>aa5c8cc6ac6a4d5f5a1d26ddf2ab71fbf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>i_alpha</name>
      <anchorfile>additional__input__none__impl_8h.html</anchorfile>
      <anchor>a1ad6f4bf1f6cfcbfa432124040563c3e</anchor>
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
    <name>address_list_entry</name>
    <filename>population__table_8h.html</filename>
    <anchor>structaddress__list__entry</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>row_length</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a358c3d5fb0251de6aa4e93494be8d7f0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>address</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a2e8ba6ab7ff064d79ef52417c492d38e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>all_but_me</name>
    <filename>connection__generator__all__but__me_8h.html</filename>
    <anchor>structall__but__me</anchor>
  </compound>
  <compound kind="struct">
    <name>all_but_me_conf</name>
    <filename>connection__generator__all__but__me_8h.html</filename>
    <anchor>structall__but__me__conf</anchor>
  </compound>
  <compound kind="struct">
    <name>all_to_all</name>
    <filename>connection__generator__all__to__all_8h.html</filename>
    <anchor>structall__to__all</anchor>
  </compound>
  <compound kind="struct">
    <name>alpha_params_t</name>
    <filename>synapse__types__alpha__impl_8h.html</filename>
    <anchor>structalpha__params__t</anchor>
  </compound>
  <compound kind="struct">
    <name>alpha_state_t</name>
    <filename>synapse__types__alpha__impl_8h.html</filename>
    <anchor>structalpha__state__t</anchor>
    <member kind="variable">
      <type>input_t</type>
      <name>lin_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a253cb401fd1c2188fb435ffab13eba04</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exp_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a6078f398c1d684a158d1f2858e091033</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>dt_divided_by_tau_sqr</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>af3b40b0c489ccdb3ad0c82c037b523d0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>decay_t</type>
      <name>decay</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a32f6514c5d3f974068433464d9e65f67</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>q_buff</name>
      <anchorfile>synapse__types__alpha__impl_8h.html</anchorfile>
      <anchor>a291abdeb86c6ce687eba035ca09f425c</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>bitfield_info_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structbitfield__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>bitfield_recording_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structbitfield__recording__t</anchor>
  </compound>
  <compound kind="struct">
    <name>bitfield_values_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structbitfield__values__t</anchor>
  </compound>
  <compound kind="struct">
    <name>change_params</name>
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <anchor>structchange__params</anchor>
  </compound>
  <compound kind="struct">
    <name>combined_provenance</name>
    <filename>structcombined__provenance.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_backgrounds_queued</name>
      <anchorfile>structcombined__provenance.html</anchorfile>
      <anchor>a9381d8e99b4a3369d547b4acd10c3b3d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_background_queue_overloads</name>
      <anchorfile>structcombined__provenance.html</anchorfile>
      <anchor>ad8a8981effe382266cc0a6387e818005</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>common_priorities</name>
    <filename>structcommon__priorities.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>sdp</name>
      <anchorfile>structcommon__priorities.html</anchorfile>
      <anchor>a52f4118b696b363a7df6cfc7c4d18083</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>dma</name>
      <anchorfile>structcommon__priorities.html</anchorfile>
      <anchor>a81ff06f46e55f58109477a18f0f54b82</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>timer</name>
      <anchorfile>structcommon__priorities.html</anchorfile>
      <anchor>aa95583081515d60e30a8e99c00bb1965</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>common_regions</name>
    <filename>structcommon__regions.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>system</name>
      <anchorfile>structcommon__regions.html</anchorfile>
      <anchor>ad8d25f5ee7bc5843e21f33125eead392</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>provenance</name>
      <anchorfile>structcommon__regions.html</anchorfile>
      <anchor>a2012b068acb03a2ff0a818076a53f44f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>profiler</name>
      <anchorfile>structcommon__regions.html</anchorfile>
      <anchor>a5fd6980960a99edf8a3a6ee8662b9257</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>recording</name>
      <anchorfile>structcommon__regions.html</anchorfile>
      <anchor>a3403d749cb8381c5669d3a46aab208fb</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>connection_builder_config_t</name>
    <filename>synapse__expander_8c.html</filename>
    <anchor>structconnection__builder__config__t</anchor>
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
      <type>initialize_connector_func *</type>
      <name>initialize</name>
      <anchorfile>connection__generator_8c.html</anchorfile>
      <anchor>a05e8e9c3a497781e378052ef25fb1ef1</anchor>
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
    <name>connector</name>
    <filename>structconnector.html</filename>
    <member kind="variable">
      <type>lc_shape_t</type>
      <name>kernel</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>ac8409f536dea382a509f2f06322c8b19</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>lc_shape_t</type>
      <name>padding</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a3a36ec47bd4df6053e40aab9fc9b0bbc</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>positive_synapse_type</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a72d74286cbe3c754229ea5d8fbd1c9a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>negative_synapse_type</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>ac8b1802bf784ffd946e6bfadfc1bd948</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>delay_stage</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>accfda9315085fd47ca9b0cbe6b11ab2f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>delay</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a47cdb4667672dbf1cdd4e839dcbf966a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>kernel_index</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a30afb0fc4a449a570621d9bd97625ccb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>stride_height_div</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a43a57ea51e53f42c3055c23b4f3a1dcd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>stride_width_div</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a1ad9114482d14cf23b130daa314104f3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>pool_stride_height_div</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>af40a7ac88a607a17da50fbc92b18b1c2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>pool_stride_width_div</name>
      <anchorfile>structconnector.html</anchorfile>
      <anchor>a0e9fc7db73985b954e8c8adf42e282c3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>conv_config</name>
    <filename>structconv__config.html</filename>
  </compound>
  <compound kind="struct">
    <name>cs_id_index_t</name>
    <filename>current__source_8h.html</filename>
    <anchor>structcs__id__index__t</anchor>
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
    <name>dc_source_t</name>
    <filename>current__source__dc_8h.html</filename>
    <anchor>structdc__source__t</anchor>
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
      <name>n_colour_bits</name>
      <anchorfile>delay__extension_8h.html</anchorfile>
      <anchor>a720c7d3fc7c1875823ccd6e4f936fd5e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>delay_value</name>
    <filename>matrix__generator__common_8h.html</filename>
    <anchor>structdelay__value</anchor>
  </compound>
  <compound kind="struct">
    <name>div_const</name>
    <filename>structdiv__const.html</filename>
  </compound>
  <compound kind="struct">
    <name>dma_buffer</name>
    <filename>structdma__buffer.html</filename>
    <member kind="variable">
      <type>synaptic_row_t</type>
      <name>sdram_writeback_address</name>
      <anchorfile>structdma__buffer.html</anchorfile>
      <anchor>a7663f1eea61dda1540ac1a8641040d0b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>spike_t</type>
      <name>originating_spike</name>
      <anchorfile>structdma__buffer.html</anchorfile>
      <anchor>a3513c98a97e75598a54b33dcde34a12c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_bytes_transferred</name>
      <anchorfile>structdma__buffer.html</anchorfile>
      <anchor>a764511923c4c18e2c1303c4386aaf5e3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>colour</name>
      <anchorfile>structdma__buffer.html</anchorfile>
      <anchor>ad5b25dca0387e7c4debcd39f9932ea15</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>colour_mask</name>
      <anchorfile>structdma__buffer.html</anchorfile>
      <anchor>ae07dbaaac8f55342c93dba29f9cd3d9a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>synaptic_row_t</type>
      <name>row</name>
      <anchorfile>structdma__buffer.html</anchorfile>
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
    <filename>exp__synapse__utils_8h.html</filename>
    <anchor>structexp__params__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>tau</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>a86cbc5a5d1b545e9f004a6c78b3e47a9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>init_input</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>ab9f760588e813ff3fda651a1f2667e2d</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>exp_state_t</name>
    <filename>exp__synapse__utils_8h.html</filename>
    <anchor>structexp__state__t</anchor>
    <member kind="variable">
      <type>decay_t</type>
      <name>decay</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>a0fec90ff56755eb65c097f5557b28266</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>decay_t</type>
      <name>init</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>a496af27ea8ca909f1a97adc522410cb9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>synaptic_input_value</name>
      <anchorfile>exp__synapse__utils_8h.html</anchorfile>
      <anchor>a1761fa531c92816be45a95a44e5f9411</anchor>
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
  </compound>
  <compound kind="struct">
    <name>fixed_post_params</name>
    <filename>connection__generator__fixed__post_8h.html</filename>
    <anchor>structfixed__post__params</anchor>
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
  </compound>
  <compound kind="struct">
    <name>fixed_pre</name>
    <filename>connection__generator__fixed__pre_8h.html</filename>
    <anchor>structfixed__pre</anchor>
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
    <name>fixed_stdp_synapse</name>
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <anchor>structfixed__stdp__synapse</anchor>
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
      <type>UREAL</type>
      <name>ticks_per_ms</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a7c28ee6e0f3f9ee952400112f7ea2c82</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>slow_rate_per_tick_cutoff</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ac5efb799fc72db5752921c90667b5404</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>fast_rate_per_tick_cutoff</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a2ab562cb1f5e281f23847934ec9e7ddc</anchor>
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
      <type>uint32_t</type>
      <name>max_spikes_per_tick</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a84009cf1a8334d0129c8b9dedaad4f9b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_colour_bits</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1b18e5c964abcc146e709319f2650948</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>rng_seed_t</type>
      <name>spike_source_seed</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aec7bae9f7db03e42be908930a8b67c20</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>input_type_params_t</name>
    <filename>input__type__none_8h.html</filename>
    <anchor>structinput__type__params__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rev_E</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>aed5e62439f9cc3e15745613d1eb75be4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rev_I</name>
      <anchorfile>input__type__none_8h.html</anchorfile>
      <anchor>a0cfe5b36ead258b16787a37b25dc1f7a</anchor>
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
    <member kind="variable">
      <type>uint16_t</type>
      <name>weightsPresent</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a70f80ef8f5497723306b27b521e3b539</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>delaysPresent</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>a61c278595d8c935eb49bde64137e1ba5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>kernelWeightsAndDelays</name>
      <anchorfile>connection__generator__kernel_8h.html</anchorfile>
      <anchor>af812d0ccba12a11f928d6ecbfca0e48f</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>key_atom_info_t</name>
    <filename>sp__structs_8h.html</filename>
    <anchor>structkey__atom__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>key_config</name>
    <filename>spike__processing__fast_8h.html</filename>
    <anchor>structkey__config</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a7a3e5253ffa546cba5f9e83406fa7836</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a37c12d1b1228f05b534697bddb055325</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>spike_id_mask</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a0d677725bdacf0d86911fd400fea30b5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>colour_shift</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>af696358bad26f021081f06a403fdf835</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>self_connected</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a62e84dad881a32b0dc9621b7404d8405</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>key_info</name>
    <filename>structkey__info.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>a6cf89fd230b00411df3913bdd5827da5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>abea6254272a206f71eec3193ecff7ac8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>start</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>a5d509292c890a4f5605f9dbda15515ee</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_colour_bits</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>a1598452d31a27f1612568b844ac4db23</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>a66e01e8b78c896f2184b0f2186645f0b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>core_mask</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>ac559a6f7ae59540a0e7a6649ca964bae</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask_shift</name>
      <anchorfile>structkey__info.html</anchorfile>
      <anchor>a70334334559700beb1181c21ee6812d8</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>lc_coord_t</name>
    <filename>structlc__coord__t.html</filename>
  </compound>
  <compound kind="struct">
    <name>lc_shape_t</name>
    <filename>structlc__shape__t.html</filename>
  </compound>
  <compound kind="struct">
    <name>limits</name>
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <anchor>structlimits</anchor>
  </compound>
  <compound kind="struct">
    <name>local_only_config</name>
    <filename>local__only_8c.html</filename>
    <anchor>structlocal__only__config</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>log_n_neurons</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>acd8bf03864a1753052ee74726b4854d0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>log_n_synapse_types</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a25b1870522b9ec44a3a3193ad54697ba</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>log_max_delay</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a19c890902fe8ff50831447e457d24047</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>input_buffer_size</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a7e00c9c42dc3e89601f803347a85b8e5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>clear_input_buffer</name>
      <anchorfile>local__only_8c.html</anchorfile>
      <anchor>a2b3b85de200ef85472a80d9b3007ade8</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>local_only_provenance</name>
    <filename>local__only_8h.html</filename>
    <anchor>structlocal__only__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_spikes_received_per_timestep</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>ae3c329f63bc4ea6940b93712c1de6f9c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes_dropped</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>ae17c734c99ed4f4b6f64123dba8660ab</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes_lost_from_input</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>ab8f54ed3e9a7c237fe137d083dda8161</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_input_buffer_size</name>
      <anchorfile>local__only_8h.html</anchorfile>
      <anchor>a6d3e0cb5b61c58cdfd3b43e66226e01c</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>master_population_table_entry</name>
    <filename>population__table_8h.html</filename>
    <anchor>structmaster__population__table__entry</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>key</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a0afdbef67c9cba4231a9c8cc63e0c005</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a5d5364d69a3eb267eba9b0e47ffd1db7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>start</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>afb309e71903c16b95d149973e753b490</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_colour_bits</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a8dbf8ef74605e734a08c4b376959215e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a1b52e9a32daa7fddff954e66cbd3bd4e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>core_mask</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ae59418b8cf6553d964c4b5b4e5744b94</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>mask_shift</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>aee21924d6d59167beb18c026e986f485</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_neurons</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>a2196632025af2e0113f8cfd4479463f1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_words</name>
      <anchorfile>population__table_8h.html</anchorfile>
      <anchor>ab9d13dcb500adc5e34abdff7de94ba2a</anchor>
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
      <type>initialize_matrix_func *</type>
      <name>initialize</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>a364a3eede465159244adb4b330713a22</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>write_synapse_func *</type>
      <name>write_synapse</name>
      <anchorfile>matrix__generator_8c.html</anchorfile>
      <anchor>ac3ed4f419c523509c68803f006a1c8ae</anchor>
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
    <name>matrix_generator_neuromodulation</name>
    <filename>matrix__generator__neuromodulation_8h.html</filename>
    <anchor>structmatrix__generator__neuromodulation</anchor>
  </compound>
  <compound kind="union">
    <name>matrix_generator_neuromodulation.__unnamed19__</name>
    <filename>matrix__generator__neuromodulation_8h.html</filename>
    <anchor>unionmatrix__generator__neuromodulation_8____unnamed19____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>synaptic_matrix</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>af6b400c26840513b7ee58df3bf0ac2be</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synaptic_matrix_offset</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>adcfd35c31907352e33cd6f35ef1fb389</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_generator_stdp_data_t</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>structmatrix__generator__stdp__data__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_row_n_synapses</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a5373ffe70ce452ba9bb3f76d506b7ed1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_delayed_row_n_synapses</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ad1e8ca16398cc8fc3414ef587d7b6739</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_row_n_words</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>abd7ab500589a86984b976070bc626b29</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_delayed_row_n_words</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a4f6423f80ded8e29e357b6b5cb9a6e7d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a1397a13cdf7986fe0dc619643b7f2e35</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ae24d1dfe8862caee856ac234da3f8c51</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aef196080cb2260eaca3cc93a38385a50</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_stage</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a14527414e8f4cc7e50b568075162f6cc</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_delay_per_stage</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ace136fe2521eb720c36274494ca3d6bb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delay_bits</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a6ccfcbaddf0bbe569448ea56534b49cb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_neurons</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a473d65f4a7583a8f9166549b15a2ba07</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_neurons_per_core</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>abe6c585e4aa85cb2bbe7a201a3618ee1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_half_words_per_pp_row_header</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>aaf18d9fbe16ef43e0a03a2a6bf6eec8c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_half_words_per_pp_synapse</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a9f0a9c8b5ab09642db74da57a9404f87</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>weight_half_word</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>ac39c09c2359f42c6423c6abb3269bf4c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>first_word_is_row_index</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a3d3577ee274c584ba90d55ea61d3fb46</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>row_offset</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>af36433df7b71fb7bf05f0b2497ac16b3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>matrix_generator_stdp_data_t.__unnamed25__</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>unionmatrix__generator__stdp__data__t_8____unnamed25____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>synaptic_matrix</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>af6b400c26840513b7ee58df3bf0ac2be</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synaptic_matrix_offset</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>adcfd35c31907352e33cd6f35ef1fb389</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>matrix_generator_stdp_data_t.__unnamed27__</name>
    <filename>matrix__generator__stdp_8h.html</filename>
    <anchor>unionmatrix__generator__stdp__data__t_8____unnamed27____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>delayed_synaptic_matrix</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>afe6ef05d5c6b9526753307f711cd2917</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delayed_matrix_offset</name>
      <anchorfile>matrix__generator__stdp_8h.html</anchorfile>
      <anchor>a1bdd384087e001d00dfc05da0ecfa5c2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_generator</name>
    <filename>matrix__generator_8c.html</filename>
    <anchor>structmatrix__generator</anchor>
  </compound>
  <compound kind="struct">
    <name>matrix_generator_weight_changer</name>
    <filename>matrix__generator__weight__changer_8h.html</filename>
    <anchor>structmatrix__generator__weight__changer</anchor>
  </compound>
  <compound kind="union">
    <name>matrix_generator_weight_changer.__unnamed29__</name>
    <filename>matrix__generator__weight__changer_8h.html</filename>
    <anchor>unionmatrix__generator__weight__changer_8____unnamed29____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>synaptic_matrix</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>af6b400c26840513b7ee58df3bf0ac2be</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synaptic_matrix_offset</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>adcfd35c31907352e33cd6f35ef1fb389</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>matrix_genetator_static_data_t</name>
    <filename>matrix__generator__static_8h.html</filename>
    <anchor>structmatrix__genetator__static__data__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_row_n_words</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>ab17ad26a258f2bf34d26b5324ab5b0d1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_delayed_row_n_words</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a0b9ac6ca34707b71f0325e2b51a89e66</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a023b645b884bb752059cebd4f26b5b5e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type_bits</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>ad649241d0bf22e45459703b93954468e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_index_bits</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a078996ab63e0271dd437881d65d17414</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_stage</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a268f13326b542ca0e08352d4b8ddca9a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_delay_per_stage</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>abefb1ff584bf309aa6cc0633f099205a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delay_bits</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a5f7f6082304d4ebd50bfd8b48718ab71</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_neurons</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a9b3800fcbb5cf9d5670d6735d5e06c89</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_neurons_per_core</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a1a17ebd5b4ccb7795574a8b227fd03e4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>matrix_genetator_static_data_t.__unnamed21__</name>
    <filename>matrix__generator__static_8h.html</filename>
    <anchor>unionmatrix__genetator__static__data__t_8____unnamed21____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>synaptic_matrix</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>af6b400c26840513b7ee58df3bf0ac2be</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synaptic_matrix_offset</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>adcfd35c31907352e33cd6f35ef1fb389</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>matrix_genetator_static_data_t.__unnamed23__</name>
    <filename>matrix__generator__static_8h.html</filename>
    <anchor>unionmatrix__genetator__static__data__t_8____unnamed23____</anchor>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>delayed_synaptic_matrix</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>afe6ef05d5c6b9526753307f711cd2917</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>delayed_matrix_offset</name>
      <anchorfile>matrix__generator__static_8h.html</anchorfile>
      <anchor>a1bdd384087e001d00dfc05da0ecfa5c2</anchor>
      <arglist></arglist>
    </member>
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
    <name>neuromodulated_synapse_t</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structneuromodulated__synapse__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuromodulation_data_t</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structneuromodulation__data__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_core_parameters</name>
    <filename>neuron_8c.html</filename>
    <anchor>structneuron__core__parameters</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_current_source_t</name>
    <filename>current__source_8h.html</filename>
    <anchor>structneuron__current__source__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_impl_t</name>
    <filename>neuron__impl__stoc__sigma_8h.html</filename>
    <anchor>structneuron__impl__t</anchor>
    <member kind="variable">
      <type>UFRACT</type>
      <name>tau_recip</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a160c0c5aedbfdf315dd9f49301f215bc</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>bias</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a9ee1ffbb56f496e2051b7fd997a416fb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>t_refract</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a23e1b3358de7aa4fc8ee02cd09fc1e62</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>refract_timer</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>aab41b75883f25efc679c83c42cd77cc4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>mars_kiss64_seed_t</type>
      <name>random_seed</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a2c2d6827f3442df74b84e01e8ecd7f06</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>inputs</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a25914975ca586ee9b1fe641d18a7b9ad</anchor>
      <arglist>[2]</arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_membrane</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a9de0a8c85cb8426915b83891e66d0a01</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_reset</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a4e3f9b433ea7a6130bd04c0423817b6d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>tau</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>a7c8a2489d4bac187f5a32fc081d64d34</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>alpha</name>
      <anchorfile>neuron__impl__stoc__sigma_8h.html</anchorfile>
      <anchor>ac8d2b942c5540605e94dae85d560a790</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_param_item_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structneuron__param__item__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_param_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structneuron__param__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_params_struct_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structneuron__params__struct__t</anchor>
  </compound>
  <compound kind="struct">
    <name>neuron_params_t</name>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <anchor>structneuron__params__t</anchor>
    <member kind="variable">
      <type>UREAL</type>
      <name>tau_ms</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a50a7b399c9d5b99abef66aa751692c7a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>time_step</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a6d28ebcdd47a7628df5f538f5e5b60a6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>bias</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a1e7bce63899fea4ca8689094b1751c68</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>refract_init</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a9411633446c19d345ffadaa40f409435</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>mars_kiss64_seed_t</type>
      <name>random_seed</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a504704f3502ce97768d4a563b92dc5c3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_init</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a74e15e71db3d2e1a31cd86ec8339a2c0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_reset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>abf6a65a8f972971302f597cf4d7fad72</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>tau</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a3877ff4af421b226018173d6e65010a1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>tau_refract</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a69b47bf8aad4ffc4420bbc1f5020ac0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>alpha</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a1a2b165694ee203c08c3bde620a3ed2a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_init</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a01195d3e2b315b7049b25bed7a00f322</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>c_m</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a0d2e44ce37bdc89bdeaba22c3fc65903</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>tau_m</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>acd02a68c932cc69f2815114f26f1609c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>I_offset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a4b4a2ba9fba6d6f10d8ef1e1c851a39e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_reset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a1b77e28a1ebe5e091767984d96a1e41f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>T_refract_ms</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a2a4cc8608f712cd69e40daa4bcecb9b9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>refract_timer_init</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ac2ffdee96e7211c98c8a5465cb277fd6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>time_step</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a6d28ebcdd47a7628df5f538f5e5b60a6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>next_h</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a44341613a6482efe24379ae9a3c758d3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rest</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a390f6f7e76ae18b982c519ad517e74ad</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_provenance</name>
    <filename>structneuron__provenance.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>current_timer_tick</name>
      <anchorfile>structneuron__provenance.html</anchorfile>
      <anchor>a7971d970224cbcc61d40e13ebd0139cb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_tdma_misses</name>
      <anchorfile>structneuron__provenance.html</anchorfile>
      <anchor>ae102e3055f07cead0ad5a1b4adf08578</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>earliest_send</name>
      <anchorfile>structneuron__provenance.html</anchorfile>
      <anchor>aac360057b8cb583cfb0ea6cff69b5429</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>latest_send</name>
      <anchorfile>structneuron__provenance.html</anchorfile>
      <anchor>afc7ad34d9d4b4447fee327786e0a1078</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_recording_header_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structneuron__recording__header__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_recorded_vars</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>abedd25f4658e60246836b650b8432a7b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_bitfield_vars</name>
      <anchorfile>neuron__recording_8h.html</anchorfile>
      <anchor>aceb45219931c687ba2595c66b9561e18</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_regions</name>
    <filename>structneuron__regions.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>core_params</name>
      <anchorfile>structneuron__regions.html</anchorfile>
      <anchor>aa2f7d26e8899ab7b5460127b53161bd2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>neuron_params</name>
      <anchorfile>structneuron__regions.html</anchorfile>
      <anchor>a5beccf8bfe6d61fc1ea0b2cc1981c526</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>current_source_params</name>
      <anchorfile>structneuron__regions.html</anchorfile>
      <anchor>a7978e1f6206107728a1bee7524fa7fc8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>neuron_recording</name>
      <anchorfile>structneuron__regions.html</anchorfile>
      <anchor>a5eb67797af3ac013b128589af3237784</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>initial_values</name>
      <anchorfile>structneuron__regions.html</anchorfile>
      <anchor>a5dacc39c68db7093e1d086b404a9a112</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neuron_t</name>
    <filename>neuron__model__lif__impl_8h.html</filename>
    <anchor>structneuron__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>V_membrane</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ad66d54c7a07b1786b0d03888ba1c487d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>R_membrane</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a8d199c1f0e0423ae3707530f872afc75</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>I_offset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>afa7f374c044dc5b6f4c0158ea694010e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>refract_timer</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>affef55f4b097428004fad494ffaa7a26</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_reset</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a0c21f2095b2338097db6a4de641a9b0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>T_refract</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a552b3d69763d3e600964e6a1ee7a5c89</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>this_h</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ac81d28edfc234c0304748c166baeb0ac</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>reset_h</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a1d7622da6c04a63fde21386757b3b332</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>V_rest</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>a33437019fe16a8c9bde9773714eee263</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>exp_TC</name>
      <anchorfile>neuron__model__lif__impl_8h.html</anchorfile>
      <anchor>ad8b828cd0ae1cfcd20f1493d629fbb81</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>neurons_provenance</name>
    <filename>c__main__neurons_8c.html</filename>
    <anchor>structneurons__provenance</anchor>
  </compound>
  <compound kind="struct">
    <name>nm_final_state_t</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structnm__final__state__t</anchor>
  </compound>
  <compound kind="struct">
    <name>nm_params_t</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structnm__params__t</anchor>
    <member kind="variable">
      <type>accum</type>
      <name>weight_update_constant_component</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>ae2aee6ffe8d18e75f21c2b91d0d9e396</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>max_weight</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a318cffa49eecb584acb3dff74f0342e4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>min_weight</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>af76e9f3f4fd2f6c2e1071aaf7226868b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>nm_post_trace_t</name>
    <filename>post__events__with__da_8h.html</filename>
    <anchor>structnm__post__trace__t</anchor>
  </compound>
  <compound kind="struct">
    <name>nm_update_state_t</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structnm__update__state__t</anchor>
  </compound>
  <compound kind="struct">
    <name>noisy_current_source_t</name>
    <filename>current__source__noisy_8h.html</filename>
    <anchor>structnoisy__current__source__t</anchor>
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
    <name>param_generator_exponential_clipped</name>
    <filename>param__generator__exponential__clipped_8h.html</filename>
    <anchor>structparam__generator__exponential__clipped</anchor>
  </compound>
  <compound kind="struct">
    <name>param_generator_exponential_clipped_params</name>
    <filename>param__generator__exponential__clipped_8h.html</filename>
    <anchor>structparam__generator__exponential__clipped__params</anchor>
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
      <type>initialize_param_func *</type>
      <name>initialize</name>
      <anchorfile>param__generator_8c.html</anchorfile>
      <anchor>a126b6347bbad0c735f3c207060cf007a</anchor>
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
      <type>accum</type>
      <name>min_weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a5e836cb37e45b87e7be6b6f8aa4d8712</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>max_weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a9bb6d4801276253265ac4a027c9771ed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>a2_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a47f87b538e43e839af120a7a83de5549</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>a2_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>ab2bcedb9602d0d051de12c6fa6847416</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>a3_plus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a201d7088a2aa9894c7ceddcd87ba8aaf</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>accum</type>
      <name>a3_minus</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a6295ace66cb47cb91bcf7bfa02621f82</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>poisson_extension_provenance</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structpoisson__extension__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_saturations</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a55c4a2fa564698252c27abd2d94bd51a</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>pop_table_config_t</name>
    <filename>population__table_8h.html</filename>
    <anchor>structpop__table__config__t</anchor>
  </compound>
  <compound kind="struct">
    <name>pop_table_lookup_result_t</name>
    <filename>population__table_8h.html</filename>
    <anchor>structpop__table__lookup__result__t</anchor>
  </compound>
  <compound kind="struct">
    <name>post_event_history_t</name>
    <filename>post__events__with__weight__change_8h.html</filename>
    <anchor>structpost__event__history__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count_minus_one</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a55510f69f9fd514e9c470fedb286a3e6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>times</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a5f4bd9d580b1661446fcd71ea2512821</anchor>
      <arglist>[MAX_POST_SYNAPTIC_EVENTS]</arglist>
    </member>
    <member kind="variable">
      <type>post_trace_t</type>
      <name>traces</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>af97afea1a11707f22b03a459cae5d8b0</anchor>
      <arglist>[MAX_POST_SYNAPTIC_EVENTS]</arglist>
    </member>
    <member kind="variable">
      <type>nm_post_trace_t</type>
      <name>traces</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a64d48dce137813444b0827139882c62b</anchor>
      <arglist>[MAX_POST_SYNAPTIC_EVENTS]</arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>dopamine_trace_markers</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a428f6a53ef30e1c3dedb4a0c106cccde</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a4506b283a8688e687dd1afc3072e0989</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>update_post_trace_t</type>
      <name>traces</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>aae6f5864a7ec1d0d68f26f9a396f9e77</anchor>
      <arglist>[MAX_EVENTS]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>post_event_window_t</name>
    <filename>post__events__with__da_8h.html</filename>
    <anchor>structpost__event__window__t</anchor>
    <member kind="variable">
      <type>post_trace_t</type>
      <name>prev_trace</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a92eee3c2aff3ee0df3e06e34c7551117</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>aaafc21255dcf5512f9c1751719ba0b0f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const post_trace_t *</type>
      <name>next_trace</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ac8965ef8cab18d79f9f329602b05c26c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const uint32_t *</type>
      <name>next_time</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a99b60b2256d73ca897abf5d0a7535962</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>num_events</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a482244387a63c58164abb271f16d90f3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time_valid</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ae21ceec3f1432649f568ae24e265185a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>nm_post_trace_t</type>
      <name>prev_trace</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>a3bbdb18adffd2514bc61b9796d59145b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const nm_post_trace_t *</type>
      <name>next_trace</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ae54b96b2bcbc0fe445d1c42a65192e8f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>dopamine_trace_markers</name>
      <anchorfile>post__events__with__da_8h.html</anchorfile>
      <anchor>ad131b5cd0825ed1698608c173fc222ef</anchor>
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
    <filename>synapse__dynamics__stdp__common_8h.html</filename>
    <anchor>structpre__event__history__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prev_time</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>ace155e5e7a0d0b2c67c5e1a802c7608e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>pre_trace_t</type>
      <name>prev_trace</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
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
    <name>provenance_data</name>
    <filename>c__main__synapses_8c.html</filename>
    <anchor>structprovenance__data</anchor>
  </compound>
  <compound kind="struct">
    <name>recording_index_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structrecording__index__t</anchor>
  </compound>
  <compound kind="struct">
    <name>recording_info_t</name>
    <filename>neuron__recording_8h.html</filename>
    <anchor>structrecording__info__t</anchor>
  </compound>
  <compound kind="struct">
    <name>recording_params_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structrecording__params__t</anchor>
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
    <name>rng_seed_t</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structrng__seed__t</anchor>
  </compound>
  <compound kind="struct">
    <name>rng_t</name>
    <filename>rng_8h.html</filename>
    <anchor>structrng__t</anchor>
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
    <name>row_changer_fixed_t</name>
    <filename>matrix__generator__weight__changer_8h.html</filename>
    <anchor>structrow__changer__fixed__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_fixed_size</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a596e88671a379f8380e22f8563d988c6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_plastic_size</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>aeb9ad9d38b1deeb054ed2f81f019774d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>int32_t</type>
      <name>fixed_plastic_data</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a094a1cde7bbea4fdde4599a86c847bef</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>row_changer_plastic_t</name>
    <filename>matrix__generator__weight__changer_8h.html</filename>
    <anchor>structrow__changer__plastic__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>plastic_plastic_size</name>
      <anchorfile>matrix__generator__weight__changer_8h.html</anchorfile>
      <anchor>a1fba7cb150c95d831b2ee4eb026cb016</anchor>
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
    <name>row_nm_fixed_t</name>
    <filename>matrix__generator__neuromodulation_8h.html</filename>
    <anchor>structrow__nm__fixed__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_fixed_size</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a25b9397bd842d53f82f3ede99a88be84</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_plastic_size</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a5df2131b6d13b40f7533de086082ae6d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>fixed_plastic_data</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a43ff0fc36cdae25f737870d164c5ab9a</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>row_nm_plastic_t</name>
    <filename>matrix__generator__neuromodulation_8h.html</filename>
    <anchor>structrow__nm__plastic__t</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>plastic_plastic_size</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a5b941faa85b5426befa036209d46a6f1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_type</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>a24c64bb4fb33311c61c8fda94efa08b0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>is_reward</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>ab4303a4693c2c76bcf62435f45a813f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>is_neuromodulation</name>
      <anchorfile>matrix__generator__neuromodulation_8h.html</anchorfile>
      <anchor>ad0be7518890904ee78bc08d1ab2729c6</anchor>
      <arglist></arglist>
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
    <name>sdram_bitfield_recording_data_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structsdram__bitfield__recording__data__t</anchor>
  </compound>
  <compound kind="struct">
    <name>sdram_config</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structsdram__config</anchor>
    <member kind="variable">
      <type>uint8_t *</type>
      <name>address</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a2f51993cda9430f33c933fcddca3c3ed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>size_in_bytes</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a12258fe85743f525833bd124d9e1fb05</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_synapse_cores</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ac71da842b9ee9030342176197e40ba3b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t *</type>
      <name>address</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a86b526324ed1f6013de23834e46a28b6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>time_for_transfer_overhead</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a7c86397a4475d693a4a04a95e5102af1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>offset</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a920cf60511ac965b613682744fae9f62</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>weights</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a0bd97541f14b0a0db1c8da7c5994418f</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>sdram_variable_recording_data_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structsdram__variable__recording__data__t</anchor>
  </compound>
  <compound kind="struct">
    <name>source_dim</name>
    <filename>structsource__dim.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>size_per_core</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>a7989071664e4045d8617a8ae74ac9ead</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cum_size_per_core</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>a62063c8235bd51c3e0d80fdd25a55946</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>cum_size_per_core_div</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>a1201234f65c45f17831f9f6000a219b7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cores</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>aa1f76993810850656d7e2f92089592c7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cum_cores</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>a56b4221e996bf0923d2dfe741ccf4653</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>cum_cores_div</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>ade7c92c4112d50b8a34d519f6562b905</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>size_last_core</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>aa000f63b07ba27607c9692a52d7481a5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cum_size_last_core</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>acd6107e951141a65421ff4e305fbf12a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>cum_size_last_core_div</name>
      <anchorfile>structsource__dim.html</anchorfile>
      <anchor>a23e1924d244d596ee21f153f8f77e5b4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>source_expand_details</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structsource__expand__details</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>count</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a0b22dacb098532eb13061823df198d9b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>source_info</type>
      <name>info</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa148724471d5c6680c4a1ad0a7182ced</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>source_expand_region</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structsource__expand__region</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>rate_changed</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a536780c6b007db0857d07656546a8fb2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>source_info</name>
    <filename>spike__source__poisson_8c.html</filename>
    <anchor>structsource__info</anchor>
    <member kind="variable">
      <type>key_info</type>
      <name>key_info</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a10205e471662aeaacbd4ac5f73702d01</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>source_height_per_core</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a6a0cfce18d8a4b0c738382e3d606b883</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>source_width_per_core</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a788c3de5e34b6b722bf280ea0da9b02c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>source_height_last_core</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a1dc7836a1e8ffc851d0f6fb5be61ca3a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>source_width_last_core</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>ab99fcf6dc30c384eb76c78c0920df682</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cores_per_source_height</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a70489cbc6f51bfd52a9ee6f3df515c15</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>cores_per_source_width</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a23dbf35c89be544f1185d56fe13d1003</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>source_width_div</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>aa07db897fd60e4c32da903dcae904d44</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>source_width_last_div</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a0bdcea89bdf47b39d1d80db3b2680c47</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>div_const</type>
      <name>cores_per_width_div</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a73e54ba950e24393e9ae6c99fe51700a</anchor>
      <arglist></arglist>
    </member>
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
      <type>source_details</type>
      <name>details</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a56c2077f5085d9d86a1a5a39d62a9029</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>spike_processing_fast_provenance</name>
    <filename>spike__processing__fast_8h.html</filename>
    <anchor>structspike__processing__fast__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_input_buffer_overflows</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a7c97c1b4f48b14653063932276bff106</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_dmas_complete</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a3e4894fc527364f0d95f4ef67304cec7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes_processed</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>aa11f31317d1d3bc2c53f7471a2fbd338</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_rewires</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a5d9089dc46eecff324a8477701bcc289</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_dropped_from_lateness</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a100355afe9d63e3f034084db0a90fa31</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_filled_input_buffer_size</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a2611b3ece4cf313befe84da703747e8c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_spikes_received</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a941f4ad4a3cf721904fe5e6dacad0e3c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_spikes_processed</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>abcfa89e3a4aa27aadaebb85fbb4529d3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_transfer_timer_overruns</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a8c8f48422aa08e54559b1fb06c080d07</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_skipped_time_steps</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a6d75639156aae9262f4985af1eed3b4f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_transfer_timer_overrun</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>ad54eed3177f0c24003d53368aac34005</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>earliest_receive</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>ada0587dfdf0b6c93fd84124e948e0880</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>latest_receive</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>af092c1094a787efc5ecb2b5d78875b90</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_spikes_overflow</name>
      <anchorfile>spike__processing__fast_8h.html</anchorfile>
      <anchor>a16b051ee2aa9d8627aa7067590241554</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>spike_processing_provenance</name>
    <filename>spike__processing_8h.html</filename>
    <anchor>structspike__processing__provenance</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_input_buffer_overflows</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a53b1ff57c5cb526a73417807de4fe804</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_dmas_complete</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>ade12bada94a01219c31fc5a1fe24a5eb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_spikes_processed</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a209ea3daffb04594e08a5e3a246071f0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_rewires</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>a795ba93fd7814602538d95798bd8cead</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_packets_dropped_from_lateness</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>abd7aef77962476fc8dc244aeeb6ef1cd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_filled_input_buffer_size</name>
      <anchorfile>spike__processing_8h.html</anchorfile>
      <anchor>aa20789ed98caa0f3c302e124f6166dc4</anchor>
      <arglist></arglist>
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
      <type>UREAL</type>
      <name>sqrt_lambda</name>
      <anchorfile>spike__source__poisson_8c.html</anchorfile>
      <anchor>a98c710c1c2152d5c19f41ed2ccb2094f</anchor>
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
    <filename>synapse__dynamics__stdp__common_8h.html</filename>
    <anchor>structstdp__params</anchor>
    <member kind="variable">
      <type>uint32_t</type>
      <name>backprop_delay</name>
      <anchorfile>synapse__dynamics__stdp__common_8h.html</anchorfile>
      <anchor>a06c22d077ef52c561ae4d0ea9f64d7ff</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>step_current_source_amps_t</name>
    <filename>current__source__step_8h.html</filename>
    <anchor>structstep__current__source__amps__t</anchor>
  </compound>
  <compound kind="struct">
    <name>step_current_source_times_t</name>
    <filename>current__source__step_8h.html</filename>
    <anchor>structstep__current__source__times__t</anchor>
  </compound>
  <compound kind="struct">
    <name>structural_recording_values_t</name>
    <filename>topographic__map__impl_8c.html</filename>
    <anchor>structstructural__recording__values__t</anchor>
  </compound>
  <compound kind="struct">
    <name>synapse_params</name>
    <filename>synapses_8c.html</filename>
    <anchor>structsynapse__params</anchor>
  </compound>
  <compound kind="struct">
    <name>synapse_provenance</name>
    <filename>structsynapse__provenance.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_pre_synaptic_events</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a8b7c4febfb5b48ff724746939fd5e8b3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_synaptic_weight_saturations</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a6fe3542191d7d2ced6bb0ad19b2b7fde</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_plastic_synaptic_weight_saturations</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a01fa00d445c9550b160386bedbd0ff68</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_ghost_pop_table_searches</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a870bc6cb94b842c5fdb3cc3e83259525</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_failed_bitfield_reads</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a7c2ef481305240d823abc418de53dec1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_invalid_master_pop_table_hits</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a66ba96fb391b707d23174767cf8c27c5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_filtered_by_bitfield</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a5ecd8b0730953e302c74d60403925a33</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_synapses_skipped</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>a39d38c88172c1869c1fa6e1915777406</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>n_late_spikes</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>ad984a0a3e70c68213bd51a73dfcd904d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>max_late_spike</name>
      <anchorfile>structsynapse__provenance.html</anchorfile>
      <anchor>acdb7619856544343a2cc33b518586d38</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_regions</name>
    <filename>structsynapse__regions.html</filename>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_params</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>ae1bf2e2f2adb01f1790000e94584ddb0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pop_table</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>a0eefb994c142e94d536c0e03f89610d8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synaptic_matrix</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>a5633999e6ac79b130867a1800059b0a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>synapse_dynamics</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>ab1541dadc38b08475e576b020ad452dd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>structural_dynamics</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>a040c474c7474b3550ba976ca6005cc31</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>bitfield_filter</name>
      <anchorfile>structsynapse__regions.html</anchorfile>
      <anchor>a7152d47f1e4518d7b127e37899657ab2</anchor>
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
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <anchor>structsynapse__row__plastic__data__t</anchor>
    <member kind="variable">
      <type>pre_event_history_t</type>
      <name>history</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>af0d2f303f8c9aa1663c98c13b53b7ed5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>plastic_synapse_t</type>
      <name>synapses</name>
      <anchorfile>synapse__dynamics__external__weight__change_8c.html</anchorfile>
      <anchor>a8ca99776251ff7551be58b738b7d5380</anchor>
      <arglist>[]</arglist>
    </member>
  </compound>
  <compound kind="union">
    <name>synapse_row_plastic_data_t.__unnamed10__</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>unionsynapse__row__plastic__data__t_8____unnamed10____</anchor>
    <member kind="variable">
      <type>neuromodulation_data_t</type>
      <name>neuromodulation</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>ad8c7885286caf80e78990f913c8c46f3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_row_plastic_data_t.__unnamed10__.__unnamed12__</name>
    <filename>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</filename>
    <anchor>structsynapse__row__plastic__data__t_8____unnamed10_____8____unnamed12____</anchor>
    <member kind="variable">
      <type>pre_event_history_t</type>
      <name>history</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a3cd15f8f2940aff879df34df4e5c2cd1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>neuromodulated_synapse_t</type>
      <name>synapses</name>
      <anchorfile>synapse__dynamics__stdp__izhikevich__neuromodulation_8c.html</anchorfile>
      <anchor>a10ce9d2dd94352c6cce78f516219421a</anchor>
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
    <name>synapse_types_params_t</name>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <anchor>structsynapse__types__params__t</anchor>
    <member kind="variable">
      <type>alpha_params_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ad823543feff17b1157436e0a29ae8f5a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>alpha_params_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>afb38d764d2ac9d255d8851853d40b21d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ad823543feff17b1157436e0a29ae8f5a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>exc2</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a5a088fb034ea4f71de588dcafd513e03</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_params_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>afb38d764d2ac9d255d8851853d40b21d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>multiplicator_init</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a65cf181b7580785ec413b8b7ded9066b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exc2_old_init</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a2da19ce57b3c82cb1b9c9c118bdcb832</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>scaling_factor</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a2b301f2f1ed46bcbdbc4fe5de4136048</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>timestep_ms</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>abba8bae897b58ed43a68e684c8a0e6e9</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>synapse_types_t</name>
    <filename>synapse__types__semd__impl_8h.html</filename>
    <anchor>structsynapse__types__t</anchor>
    <member kind="variable">
      <type>alpha_state_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>aebbb0a0a65a17b0c580f03b50fccdeed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>alpha_state_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ab566101b8fa8437032939f3b263a951b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>af5938ab9da9b4ef7ab17de4e817c6523</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>addcfd56e64defd09153ea1401a4c1b1f</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_state_t</type>
      <name>exc</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>aebbb0a0a65a17b0c580f03b50fccdeed</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_state_t</type>
      <name>exc2</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ae9976d113882ab8adc3576bc7f1e0ceb</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>exp_state_t</type>
      <name>inh</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>ab566101b8fa8437032939f3b263a951b</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>multiplicator</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a72d9546590f2bc47d6f598591059379c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>exc2_old</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a00b09975c798929e901409393d042483</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>input_t</type>
      <name>scaling_factor</name>
      <anchorfile>synapse__types__semd__impl_8h.html</anchorfile>
      <anchor>a2e454d97e37bc2abe34cb1f2043732a0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>threshold_type_params_t</name>
    <filename>threshold__type__static_8h.html</filename>
    <anchor>structthreshold__type__params__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>threshold_value</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a6e1abe871ed27b99be9a050662871898</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>UREAL</type>
      <name>prob</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>acb6480b8c89a0d8f37f0a6b1ac43d829</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>mars_kiss64_seed_t</type>
      <name>random_seed</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>adc735fc21bcd1ae87be78e94606176e1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>du_th</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a39a4a0cad4335ec0a6228e491c51b715</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>tau_th</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a8765ecbcef96af7f1564c611b7f3ae70</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>v_thresh</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a2a2c98c037d25d3e16f5fbed1f25885a</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>REAL</type>
      <name>time_step_ms</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a6618b1cdebadeb52e86c0ea33d94ea8b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>threshold_type_t</name>
    <filename>threshold__type__static_8h.html</filename>
    <anchor>structthreshold__type__t</anchor>
    <member kind="variable">
      <type>REAL</type>
      <name>threshold_value</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a8d25a3b92dbeffe773c096f0289aeb44</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>prob</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>ae90fdec13c7d2862578f4256ceab80e3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>mars_kiss64_seed_t</type>
      <name>random_seed</name>
      <anchorfile>threshold__type__static_8h.html</anchorfile>
      <anchor>a84a9a1b91768c0849b17569e73381e99</anchor>
      <arglist></arglist>
    </member>
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
    <name>type_info</name>
    <filename>type__writers_8h.html</filename>
    <anchor>structtype__info</anchor>
  </compound>
  <compound kind="struct">
    <name>uniform_params</name>
    <filename>param__generator__uniform_8h.html</filename>
    <anchor>structuniform__params</anchor>
  </compound>
  <compound kind="struct">
    <name>updatable_synapse_t</name>
    <filename>synapse__dynamics__external__weight__change_8c.html</filename>
    <anchor>structupdatable__synapse__t</anchor>
  </compound>
  <compound kind="struct">
    <name>update_post_trace_t</name>
    <filename>post__events__with__weight__change_8h.html</filename>
    <anchor>structupdate__post__trace__t</anchor>
    <member kind="variable">
      <type>int16_t</type>
      <name>weight_change</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>ab971037ac4f757aef0a704d92e4a215e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint16_t</type>
      <name>synapse_type</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>a2968c11edcf026d68895b45b473e6678</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>pre_spike</name>
      <anchorfile>post__events__with__weight__change_8h.html</anchorfile>
      <anchor>ac6d84978cf6d1b8fb4b3ea2187344800</anchor>
      <arglist></arglist>
    </member>
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
    <name>variable_recording_t</name>
    <filename>neuron__expander_8c.html</filename>
    <anchor>structvariable__recording__t</anchor>
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
      <type>accum</type>
      <name>weight</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>ad3aa87c77d2dc9e031a628ae3ff71c94</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>uint32_t</type>
      <name>weight_shift</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>aff8688b11fa9ba9fe9bb69c65095d853</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>const plasticity_weight_region_data_t *</type>
      <name>weight_region</name>
      <anchorfile>weight__multiplicative__impl_8h.html</anchorfile>
      <anchor>a037ff5bb63dd02afd72abd232bfd09ca</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="page">
    <name>index</name>
    <title>sPyNNaker: A PyNN Implementation for SpiNNaker</title>
    <filename>index.html</filename>
    <docanchor file="index.html" title="Introduction">intro</docanchor>
    <docanchor file="index.html" title="Neuron Simulation Implementation">neuron</docanchor>
    <docanchor file="index.html" title="Support Binaries">support</docanchor>
    <docanchor file="index.html" title="Preferred Citation">cite</docanchor>
  </compound>
</tagfile>
