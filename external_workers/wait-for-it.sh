#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available

set -e

TIMEOUT=15
QUIET=0
HOST=$1
PORT=$2

wait_for() {
    for i in `seq $TIMEOUT` ; do
        nc -z $HOST $PORT && break
        echo "Waiting for $HOST:$PORT... ($i)"
        sleep 1
    done
}

while getopts "qt:" opt; do
    case "$opt" in
        q) QUIET=1 ;;
        t) TIMEOUT=$OPTARG ;;
    esac
done

shift $((OPTIND-1))

if [ $# -ne 2 ]; then
    echo "Usage: $0 [-t timeout] [-q] host port"
    exit 1
fi

if [ "$QUIET" -ne 1 ]; then
    echo "Waiting for $HOST:$PORT..."
fi

wait_for
