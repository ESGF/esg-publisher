#!/usr/bin/env bash


ROOT_DIR=/autofs/nccsopen-svm1_home/mfx/MyGit/esg-publisher/tests/unit/data

find "$ROOT_DIR/MIP-DRS7/" -type f -name "*.nc" | sort | while read -r FILE; do
    # File metadata
    echo $FILE
    SIZE=$(stat -c"%s" "$FILE")
    MTIME=$(stat -c"%Z" "$FILE")

    CHECKSUM=$(sha256sum "$FILE" | awk '{print $1}')
    echo $SIZE, $MTIME, $CHECKSUM

    ## Extract CMIP6 components from path
    REL_PATH=${FILE#"$ROOT_DIR"/}

    IFS='/' read -r DRS MIP_ERA MIP INST MODEL EXP MEMBER REGION TABLE VAR_ID BRANDING_SFX GRID VERSION FILENAME <<< "$REL_PATH"

    ## Remove leading "v" from version
    VERSION_CLEAN=${VERSION#v}

    DATASET_ID="${DRS}.${MIP_ERA}.${MIP}.${INST}.${MODEL}.${EXP}.${MEMBER}.${REGION}.${TABLE}.${VAR_ID}.${BRANDING_SFX}.${GRID}.${VERSION}"

    FILE4TEST=${FILE/"$ROOT_DIR"/"\$TEST_DATA"}
    echo "${DATASET_ID} | ${FILE4TEST} | ${SIZE} | mod_time=${MTIME}.0 | checksum=${CHECKSUM} | checksum_type=SHA256" > "$ROOT_DIR/MIP-DRS7/${DATASET_ID}.map"
done
