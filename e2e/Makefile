vlsi_dir=$(abspath .)



# minimal flow configuration variables
design				?= test
tech				?= sky130
tools				?= cm
env					?= bwrc

extra				?=  # extra configs
step				?=  # step flow control


OBJ_DIR				?= $(vlsi_dir)/build-$(tech)-$(tools)/$(design)

# non-overlapping default configs
ENV_YML				?= configs-env/$(env)-env.yml
PATHS_YML			?= configs-env/$(env).yml
TECH_CONF			?= configs-tech/$(tech).yml
TOOLS_CONF			?= configs-tool/$(tools).yml

# design-specific overrides of default configs
DESIGN_CONF			?= configs-design/$(design)/common.yml
DESIGN_TECH_CONF	?= configs-design/$(design)/$(tech).yml
SIM_CONF			?= configs-design/$(design)/sim-rtl.yml
POWER_CONF			?= $(if $(findstring power-rtl,$(MAKECMDGOALS)), configs-design/$(design)/power-rtl-$(tech).yml, \
					   $(if $(findstring power-syn,$(MAKECMDGOALS)), configs-design/$(design)/power-syn-$(tech).yml,))


CONFS				?= $(PATHS_YML) $(TECH_CONF) $(TOOLS_CONF) $(DESIGN_CONF) $(DESIGN_TECH_CONF) $(SIM_CONF) $(POWER_CONF) $(extra)
HAMMER_EXTRA_ARGS	?= $(foreach conf, $(CONFS), -p $(conf)) $(step)




HAMMER_D_MK = $(OBJ_DIR)/hammer.d

build: $(HAMMER_D_MK)

$(HAMMER_D_MK):
	hammer-vlsi --obj_dir $(OBJ_DIR) -e $(ENV_YML) $(HAMMER_EXTRA_ARGS) build

sim-syn: override SIM_CONF = configs-design/$(design)/sim-syn.yml
sim-par: override SIM_CONF = configs-design/$(design)/sim-par.yml

-include $(HAMMER_D_MK)
