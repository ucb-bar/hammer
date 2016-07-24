# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

$(OBJ_SOC_RTL_V): $(OBJ_CORE_RTL_V)
	mkdir -p $(dir $@)
	cat $^ > $@
