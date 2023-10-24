#!/bin/bash

export e2e_dir=${PWD}

if [ ! -z $1 ]
then
    export PREFIX=$1
else
    export PREFIX=~/
fi

# install open-source tools
conda create -y -c litex-hub --prefix ${PREFIX}/.conda-yosys yosys=0.27_4_gb58664d44
conda create -y -c litex-hub --prefix ${PREFIX}/.conda-openroad openroad=2.0_7070_g0264023b6
conda create -y -c litex-hub --prefix ${PREFIX}/.conda-klayout klayout=0.28.5_98_g87e2def28
conda create -y -c litex-hub --prefix ${PREFIX}/.conda-signoff magic=8.3.427_0_gd624b76 netgen=1.5.250_0_g178b172

git clone https://github.com/google/skywater-pdk.git ${PREFIX}/skywater-pdk
git clone https://github.com/RTimothyEdwards/open_pdks.git ${PREFIX}/open_pdks
git clone https://github.com/rahulk29/sram22_sky130_macros ${PREFIX}/sram22_sky130_macros

# add magic to PATH for open_pdks
export PATH=${PREFIX}/.conda-signoff/bin:$PATH

# install sky130A with open_pdks
cd ${PREFIX}/open_pdks
./configure \
--enable-sky130-pdk=${PREFIX}/skywater-pdk/libraries --prefix=$PREFIX \
--disable-gf180mcu-pdk --disable-alpha-sky130 --disable-xschem-sky130 --disable-primitive-gf180mcu \
--disable-verification-gf180mcu --disable-io-gf180mcu --disable-sc-7t5v0-gf180mcu \
--disable-sc-9t5v0-gf180mcu --disable-sram-gf180mcu --disable-osu-sc-gf180mcu
make
make install

cd ${e2e_dir}

export ENV_YML=${e2e_dir}/configs-env/my-env.yml
echo "# My environment configs" > $ENV_YML
echo "# pdk" > $ENV_YML
echo "technology.sky130.sky130A: ${PREFIX}/share/pdk/sky130A" >> $ENV_YML
echo "technology.sky130.sram22_sky130_macros: ${PREFIX}/sram22_sky130_macros" >> $ENV_YML
echo "" >> $ENV_YML
echo "# tools" >> $ENV_YML
echo "synthesis.yosys.yosys_bin: ${PREFIX}/.conda-yosys/bin/yosys" >> $ENV_YML
echo "par.openroad.openroad_bin: ${PREFIX}/.conda-openroad/bin/openroad" >> $ENV_YML
echo "par.openroad.klayout_bin: ${PREFIX}/.conda-klayout/bin/klayout" >> $ENV_YML
echo "drc.klayout.klayout_bin: ${PREFIX}/.conda-klayout/bin/klayout" >> $ENV_YML
echo "drc.magic.magic_bin: ${PREFIX}/.conda-signoff/bin/magic" >> $ENV_YML
echo "lvs.netgen.netgen_bin: ${PREFIX}/.conda-signoff/bin/netgen" >> $ENV_YML