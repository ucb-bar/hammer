#!/bin/bash

# This script contains a series of hacks to make the ASAP7 process work. It should be sourced after initial extraction of the tarball.

# Modify the DRC & LVS rule decks to remove duplicate specification statements
PDK_DIR=ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5
DRC_DECK=$PDK_DIR/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs/drc/drcRules_calibre_asap7.rul
LVS_DECK=$PDK_DIR/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs/lvs/lvsRules_calibre_asap7.rul

for FORBIDDEN in "LAYOUT PATH" "LAYOUT PRIMARY" "LAYOUT SYSTEM" "DRC RESULTS DATABASE" "DRC SUMMARY REPORT" "LVS REPORT" "LVS POWER NAME" "LVS GROUND NAME"
do
    sed -i '/'"$FORBIDDEN"'/d' $DRC_DECK
    sed -i '/'"$FORBIDDEN"'/d' $LVS_DECK
done

# Make GDS's for all Vt's
ORIG_GDS=$PDK_DIR/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24.gds
$(dirname $BASH_SOURCE[0])/gds_vts.py $ORIG_GDS

# Edit the SRAM flavor of the LVS CDL to not be the same as SLVT
SRAM_CDL=$PDK_DIR/asap7libs_24.tar.bz2/asap7libs_24/cdl/lvs/asap7_75t_SRAM.cdl

sed -i 's/SL/SRAM/g' $SRAM_CDL
sed -i 's/slvt/SRAM/g' $SRAM_CDL
