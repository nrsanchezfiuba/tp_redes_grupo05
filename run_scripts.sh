#!/bin/bash

source .venv/bin/activate

BLACK_CMD="black ."
MYPY_CMD="mypy --strict ."
PYTEST_CMD="pytest --cov=src --cov-fail-under=75"

# Check input argument
if [ "$1" == "all" ] || [ -z "$1" ]; then
    $BLACK_CMD
    $MYPY_CMD
    PYTHONPATH=src $PYTEST_CMD
elif [ "$1" == "black" ]; then
    $BLACK_CMD
elif [ "$1" == "mypy" ]; then
    $MYPY_CMD
elif [ "$1" == "pytest" ]; then
    PYTHONPATH=src $PYTEST_CMD
else
    echo "Unknown command: $1"
    echo "Usage: $0 {all|black|mypy|pytest}"
    exit 1
fi
