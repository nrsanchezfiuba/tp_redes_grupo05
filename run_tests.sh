#!/bin/bash

# Set the PYTHONPATH and run pytest with coverage
PYTHONPATH=src pytest --cov=src
