#!/bin/bash

source .venv/bin/activate

PYTHONPATH=src pytest --cov=src --cov-fail-under=75
