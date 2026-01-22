#!/bin/bash
# Test script for rounding direction analysis visualization

PYTHONPATH=/Volumes/Trail/slither python3 slither/analyses/data_flow/analyses/rounding/test_rounding.py "$@"
