#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo $DIR
PARENT_DIR=$(dirname "$DIR")
echo "$PARENT_DIR"