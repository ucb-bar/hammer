vlsi_dir=$(abspath .)



# minimal flow configuration variables
design				?= test
pdk					?= sky130
tools				?= cm
env					?= bwrc

extra				?=  # extra configs
step				?=  # step flow control


OBJ_DIR				?= $(vlsi_dir)/build-$(pdk)-$(tools)/$(design)

# non-overlapping default configs
ENV_YML				?= configs-env/$(env)-env.yml
PATHS_YML			?= configs-env/$(env).yml
PDK_CONF			?= configs-pdk/$(pdk).yml
TOOLS_CONF			?= configs-tool/$(tools).yml

# design-specific overrides of default configs
DESIGN_CONF			?= configs-design/$(design)/common.yml
DESIGN_PDK_CONF	?= configs-design/$(design)/$(pdk).yml
SIM_CONF			?= $(if $(findstring sim-syn,$(MAKECMDGOALS)), configs-design/$(design)/sim-syn.yml, \
					   $(if $(findstring sim-par,$(MAKECMDGOALS)), configs-design/$(design)/sim-par.yml, \
					   configs-design/$(design)/sim-rtl.yml))
POWER_CONF			?= $(if $(findstring power-rtl,$(MAKECMDGOALS)), configs-design/$(design)/power-rtl-$(pdk).yml, \
					   $(if $(findstring power-syn,$(MAKECMDGOALS)), configs-design/$(design)/power-syn-$(pdk).yml, \
					   $(if $(findstring power-par,$(MAKECMDGOALS)), configs-design/$(design)/power-par-$(pdk).yml, \
					   ))) # default is none because these configs specify sim + syn clock period so shouldn't be included in other actions

CONFS				?= $(PATHS_YML) $(PDK_CONF) $(TOOLS_CONF) $(DESIGN_CONF) $(DESIGN_PDK_CONF) $(SIM_CONF) $(POWER_CONF) $(extra)
HAMMER_EXTRA_ARGS	?= $(foreach conf, $(CONFS), -p $(conf)) $(step)




HAMMER_D_MK = $(OBJ_DIR)/hammer.d

build: $(HAMMER_D_MK)

$(HAMMER_D_MK):
	hammer-vlsi --obj_dir $(OBJ_DIR) -e $(ENV_YML) $(HAMMER_EXTRA_ARGS) build

-include $(HAMMER_D_MK)
