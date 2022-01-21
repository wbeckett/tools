#!/bin/bash

set -e

HOST=$HAPROXY_SERVER_NAME
PORT=$4


if [ -z $HOST ]; then
  echo "Hostname not set"
  exit 1
fi

if [ -z $PORT ]; then
  echo "Port not set"
  exit 1
fi



echo "Checking $HOST"

DATA=$( timeout 10s psql -h ${HOST} -p ${PORT}  postgres -U haproxy --tuples-only -q -c "SELECT pg_is_in_recovery();" 2>&1  | sed -e "s/ //" | head -n 1  )

if [ X"$DATA" == "Xf" ]; then
  echo "Master"
else
  echo "Not Master"
  exit 1
fi

