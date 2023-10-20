#!/bin/bash

export e2e_dir=${PWD}

export INSTALL_PREFIX=/tools/scratch/nayiri/tutorial-installs

# install open-source tools
conda create -y -c litex-hub --prefix ${INSTALL_PREFIX}/.conda-yosys yosys=0.27_4_gb58664d44
conda create -y -c litex-hub --prefix ${INSTALL_PREFIX}/.conda-openroad openroad=2.0_7070_g0264023b6
conda create -y -c litex-hub --prefix ${INSTALL_PREFIX}/.conda-klayout klayout=0.28.5_98_g87e2def28
conda create -y -c litex-hub --prefix ${INSTALL_PREFIX}/.conda-signoff magic=8.3.427_0_gd624b76 netgen=1.5.250_0_g178b172

git clone https://github.com/google/skywater-pdk.git ${INSTALL_PREFIX}/skywater-pdk
git clone https://github.com/RTimothyEdwards/open_pdks.git ${INSTALL_PREFIX}/open_pdks
git clone https://github.com/rahulk29/sram22_sky130_macros ${INSTALL_PREFIX}/sram22_sky130_macros

# add magic to PATH for open_pdks
export PATH=${INSTALL_PREFIX}/.conda-signoff/bin:$PATH

# install sky130A with open_pdks
cd ${INSTALL_PREFIX}/open_pdks
./configure \
--enable-sky130-pdk=${INSTALL_PREFIX}/skywater-pdk/libraries --prefix=$INSTALL_PREFIX \
--disable-gf180mcu-pdk --disable-alpha-sky130 --disable-xschem-sky130 --disable-primitive-gf180mcu \
--disable-verification-gf180mcu --disable-io-gf180mcu --disable-sc-7t5v0-gf180mcu \
--disable-sc-9t5v0-gf180mcu --disable-sram-gf180mcu --disable-osu-sc-gf180mcu
make
make install

cd ${e2e_dir}

export ENV_YML=${e2e_dir}/configs-env/my-env.yml
echo "# My environment configs" > $ENV_YML
echo "# pdk" > $ENV_YML
echo "technology.sky130.sky130A: ${INSTALL_PREFIX}/.conda-sky130/share/pdk/sky130A" >> $ENV_YML
echo "technology.sky130.sram22_sky130_macros: ${INSTALL_PREFIX}/sram22_sky130_macros" >> $ENV_YML
echo "" >> $ENV_YML
echo "# tools" >> $ENV_YML
echo "synthesis.yosys.yosys_bin: ${INSTALL_PREFIX}/.conda-yosys/bin/yosys" >> $ENV_YML
echo "par.openroad.openroad_bin: ${INSTALL_PREFIX}/.conda-openroad/bin/openroad" >> $ENV_YML
echo "par.openroad.klayout_bin: ${INSTALL_PREFIX}/.conda-klayout/bin/klayout" >> $ENV_YML
echo "drc.klayout.klayout_bin: ${INSTALL_PREFIX}/.conda-klayout/bin/klayout" >> $ENV_YML
echo "drc.magic.magic_bin: ${INSTALL_PREFIX}/.conda-signoff/bin/magic" >> $ENV_YML
echo "lvs.netgen.netgen_bin: ${INSTALL_PREFIX}/.conda-signoff/bin/netgen" >> $ENV_YML