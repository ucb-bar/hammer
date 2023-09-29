vlsi_dir=$(abspath .)



# minimal flow configuration variables
design              ?= pass
pdk                 ?= sky130
tools               ?= cm
env                 ?= bwrc

extra               ?=  # extra configs
args                ?=  # command-line args (including step flow control)


OBJ_DIR             ?= $(vlsi_dir)/build-$(pdk)-$(tools)/$(design)

# non-overlapping default configs
ENV_YML             ?= configs-env/$(env)-env.yml
PDK_CONF            ?= configs-pdk/$(pdk).yml
TOOLS_CONF          ?= configs-tool/$(tools).yml

# design-specific overrides of default configs
DESIGN_CONF         ?= configs-design/$(design)/common.yml
DESIGN_PDK_CONF     ?= configs-design/$(design)/$(pdk).yml
SIM_CONF            ?= $(if $(findstring rtl,$(MAKECMDGOALS)), configs-design/$(design)/sim-rtl.yml, \
                       $(if $(findstring syn,$(MAKECMDGOALS)), configs-design/$(design)/sim-syn.yml, \
                       $(if $(findstring par,$(MAKECMDGOALS)), configs-design/$(design)/sim-par.yml, )))
POWER_CONF          ?= $(if $(findstring power-rtl,$(MAKECMDGOALS)), configs-design/$(design)/power-rtl-$(pdk).yml, \
                       $(if $(findstring power-syn,$(MAKECMDGOALS)), configs-design/$(design)/power-syn-$(pdk).yml, \
                       $(if $(findstring power-par,$(MAKECMDGOALS)), configs-design/$(design)/power-par-$(pdk).yml, )))

PROJ_YMLS           ?= $(PDK_CONF) $(TOOLS_CONF) $(DESIGN_CONF) $(DESIGN_PDK_CONF) $(SIM_CONF) $(POWER_CONF) $(extra)
HAMMER_EXTRA_ARGS   ?= $(foreach conf, $(PROJ_YMLS), -p $(conf)) $(args)




HAMMER_D_MK = $(OBJ_DIR)/hammer.d

build: $(HAMMER_D_MK)

$(HAMMER_D_MK):
	hammer-vlsi --obj_dir $(OBJ_DIR) -e $(ENV_YML) $(HAMMER_EXTRA_ARGS) build

-include $(HAMMER_D_MK)
