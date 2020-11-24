#!/bin/bash

cfg=~/.spynnaker.cfg

echo '[Machine]' > $cfg

if [ "x$M_ADDR}" = "x" ]; then
	echo "machineName = None" >> $cfg
	echo "version = None" >> $cfg

	echo "spalloc_server = $S_HOST" >> $cfg
	echo "spalloc_port = $S_PORT" >> $cfg
	echo "spalloc_user = $S_USER" >> $cfg
else
	echo "machineName = $M_ADDR" >> $cfg
	echo "version = $M_VERSION" >> $cfg
fi

if [ "x$V_TYPE" = "xtrue" ]; then
	echo "virtual_board = True" >> $cfg
	echo "width = $V_WIDTH" >> $cfg
	echo "height = $V_HEIGHT" >> $cfg
else
	echo "virtual_board = False" >> $cfg
	echo "width = None" >> $cfg
	echo "height = None" >> $cfg
fi

echo "time_scale_factor = $M_TSF" >> $cfg

echo '[Database]' >> $cfg

echo '[Simulation]' >> $cfg

echo '[Buffers]' >> $cfg

echo '[Mode]' >> $cfg
echo "mode = $M_MODE" >> $cfg

echo '[Reports]' >> $cfg
echo "default_report_file_path = $F_PATH" >> $cfg
echo "default_application_data_file_path = $F_PATH" >> $cfg
