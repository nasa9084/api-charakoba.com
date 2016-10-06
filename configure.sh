#!/bin/bash

while getopts :p: OPT; do
    case $OPT in
        p|+p)
            path="$OPTARG"
            ;;
        *)
            echo "usage: `basename $0` [+-p ARG} [--] ARGS..."
            exit 2
    esac
done
shift `expr $OPTIND - 1`
OPTIND=1

sed -rie "s#/path/to/app#$path#g" nginx/api.conf
