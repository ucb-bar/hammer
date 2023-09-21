vlsi_dir=$(abspath .)



# minimal flow configuration variables
design				?= test
tech				?= sky130
tools				?= cm
env					?= bwrc

extra				?=
step				?=


# sensible default configurations
OBJ_DIR				?= $(vlsi_dir)/build-$(tech)-$(tools)/$(design)
ENV_YML				?= configs-env/$(env)-env.yml
TECH_CONF			?= configs-tech/$(tech)-bwrc.yml
TOOLS_CONF			?= configs-tool/$(tools).yml
DESIGN_CONF			?= configs-design/$(design)/common.yml
DESIGN_TECH_CONF	?= configs-design/$(design)/$(tech).yml
SIM_CONF			?= configs-design/$(design)/sim.yml
POWER_CONF			?= $(if $(findstring power-rtl,$(MAKECMDGOALS)), configs-design/$(design)/power-rtl-$(tech).yml, \
					   $(if $(findstring power-syn,$(MAKECMDGOALS)), configs-design/$(design)/power-syn-$(tech).yml,))
EXTRA_CONFS			?= $(extra)


CONFS				?= $(TECH_CONF) $(TOOLS_CONF) $(DESIGN_CONF) $(DESIGN_TECH_CONF) $(SIM_CONF) $(POWER_CONF) $(EXTRA_CONFS)
HAMMER_EXTRA_ARGS	?= $(foreach conf, $(CONFS), -p $(conf)) $(step)




HAMMER_D_MK = $(OBJ_DIR)/hammer.d

build: $(HAMMER_D_MK)

$(HAMMER_D_MK): 
	hammer-vlsi --obj_dir $(OBJ_DIR) -e $(ENV_YML) $(HAMMER_EXTRA_ARGS) build


# power-rtl: override POWER_CONF ?= configs-design/$(design)/power-rtl-$(tech).yml
# power-syn: override POWER_CONF = configs-design/$(design)/power-syn-$(tech).yml

sim-syn: override SIM_CONF = configs-design/$(design)/syn-sim.yml

sim-par: override SIM_CONF = configs-design/$(design)/syn-par.yml

-include $(HAMMER_D_MK)
