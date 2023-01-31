#!/usr/bin/env bash

usage="$(basename "$0") [-h] [-v] -- Script to update necessary files for SDK version release

where:
	-h  Show help text
	-v  New SDK version"

while getopts ':hv:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    v) new_version=$OPTARG
       ;;
    :) printf "missing argument for -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
   \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done

if [ $# -eq 0 ]
  then
    echo "No SDK version is specified"
    echo "$usage" >&2
    exit;
fi

SDK_PATH="$( cd -- "$(dirname "$0")" | cd ..  >/dev/null 2>&1 ; pwd -P )"
INIT_FILE="$SDK_PATH/labelbox/__init__.py"
READTHEDOCS_CONF_FILE="$SDK_PATH/docs/source/conf.py"
CHANGELOGS_FILE="$SDK_PATH/CHANGELOG.md"

old_version=$(cat $SDK_PATH/labelbox/__init__.py | grep __version__ | cut -d '=' -f2 | tr -d ' ' | tr -d '"')

echo "New version: $new_version"
echo "Old version: $old_version"

escaped_old_version=$(echo "$old_version" | sed "s/\./\\\./g")
escaped_new_version=$(echo "$new_version" | sed "s/\./\\\./g")

sed -i "" "s/$escaped_old_version/$escaped_new_version/" $INIT_FILE
echo "Updated '$INIT_FILE'"

sed -i "" "s/$escaped_old_version/$escaped_new_version/" $READTHEDOCS_CONF_FILE
echo "Updated '$READTHEDOCS_CONF_FILE'"
echo "Successfully updated SDK version locally!"

echo "\nOpening CHANGELOGS file in text editor"
open -e $CHANGELOGS_FILE

echo "\nPlease open a PR to finish the release process using the following git commands:"
echo "\ngit add --all"
echo "git commit -m 'Preparing for $new_version release'"
echo "git push origin prep_$new_version"
