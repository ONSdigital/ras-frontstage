#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${DIR}"/.. || exit

if [ $# -eq 0 ] || [ "$1" == "" ]; then
    echo "The Design System version must be passed in as an argument."
    echo "Usage: load_templates.sh {DESIGN_SYSTEM_VERSION}"
    exit 1
else
    DESIGN_SYSTEM_VERSION="$1"
fi

TEMP_DIR=$(mktemp -d)

curl -L --url "https://github.com/ONSdigital/design-system/releases/download/$DESIGN_SYSTEM_VERSION/templates.zip" --output ${TEMP_DIR}/templates.zip
unzip ${TEMP_DIR}/templates.zip -d ${TEMP_DIR}/templates
rm -rf frontstage/templates/components
rm -rf frontstage/templates/layout
mv ${TEMP_DIR}/templates/templates/* frontstage/templates/
rm -rf ${TEMP_DIR}
