#!/usr/bin/env bash


ROOT_DIR=/nl/themis/esgf/cli137/mfx/Staged_E3SM/css03_data/

MIP_ERA="CMIP6"  # "MIP-DRS7"

FILTER_TAB='mon'

find "$ROOT_DIR/$MIP_ERA/" -type f -name "*.nc" | sort | while read -r FILE; do
    # File metadata
    echo $FILE

    ## Extract CMIP6 components from path
    REL_PATH=${FILE#"$ROOT_DIR"/}

    if [[ $MIP_ERA == "MIP-DRS7" ]]; then
        IFS='/' read -r DRS MIP_ERA MIP INST MODEL EXP MEMBER REGION TABLE VAR_ID BRANDING_SFX GRID VERSION FILENAME <<< "$REL_PATH"
        ## Remove leading "v" from version
        VERSION_CLEAN=${VERSION#v}
        DATASET_ID="${DRS}.${MIP_ERA}.${MIP}.${INST}.${MODEL}.${EXP}.${MEMBER}.${REGION}.${TABLE}.${VAR_ID}.${BRANDING_SFX}.${GRID}.${VERSION}"
        MAPFILE=$DATASET_ID
    elif [[ $MIP_ERA == "CMIP6" ]]; then
        IFS='/' read -r MIP_ERA MIP INST MODEL EXP MEMBER TABLE VAR_ID GRID VERSION FILENAME <<< "$REL_PATH"
        VERSION_CLEAN=${VERSION#v}
        DATASET_ID="${MIP_ERA}.${MIP}.${INST}.${MODEL}.${EXP}.${MEMBER}.${TABLE}.${VAR_ID}.${GRID}#${VERSION_CLEAN}"
        MAPFILE="${MIP_ERA}.${MIP}.${INST}.${MODEL}.${EXP}.${MEMBER}.${TABLE}.${VAR_ID}.${GRID}.${VERSION}"
    fi

    if [[ "$TABLE" == *"$FILTER_TAB" ]]; then
        echo "processing $FILETR_TAB"
    else
        continue
    fi

    SIZE=$(stat -c"%s" "$FILE")
    MTIME=$(stat -c"%Z" "$FILE")
    CHECKSUM=$(sha256sum "$FILE" | awk '{print $1}')
    echo $SIZE, $MTIME, $CHECKSUM

    FILE4TEST=${FILE/"$ROOT_DIR"/"\$TEST_DATA"}
    echo "${DATASET_ID} | ${FILE} | ${SIZE} | mod_time=${MTIME}.0 | checksum=${CHECKSUM} | checksum_type=SHA256" >> "${MAPFILE}.map"
done
