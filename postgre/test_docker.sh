#!/bin/bash
COMPOSE_CMD="docker compose"
if ! $COMPOSE_CMD version &> /dev/null; then
    echo "Failed"
else
    echo "Succeeded"
fi
