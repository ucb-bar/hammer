#!/bin/bash

# We need to modify the DRC & LVS rule decks to remove duplicate specification statements
PDK_DIR=ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5
DRC_DECK=$PDK_DIR/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs/drc/drcRules_calibre_asap7.rul
LVS_DECK=$PDK_DIR/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs/lvs/lvsRules_calibre_asap7.rul

for FORBIDDEN in "LAYOUT PATH" "LAYOUT PRIMARY" "LAYOUT SYSTEM" "DRC RESULTS DATABASE" "DRC SUMMARY REPORT" "LVS REPORT" "LVS POWER NAME" "LVS GROUND NAME"
do
    sed -i '/'"$FORBIDDEN"'/d' $DRC_DECK
    sed -i '/'"$FORBIDDEN"'/d' $LVS_DECK
done

# We need to make GDS's for all Vt's
GDS_BASE_NAME=$PDK_DIR/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24
ORIG_GDS=$GDS_BASE_NAME.gds

for CORNER in "R" "L" "SL"
do
    cp $ORIG_GDS ${GDS_BASE_NAME}_$CORNER.gds
    sed -i 's/_SL/_'"$CORNER"'/g' ${GDS_BASE_NAME}_$CORNER.gds
done
