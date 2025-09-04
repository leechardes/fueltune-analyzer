#!/usr/bin/env python3
"""
Setup script for FuelTune Streamlit.

This file provides backwards compatibility with older tools that don't support
pyproject.toml, but the main configuration is in pyproject.toml.
"""

from setuptools import setup

# The configuration is now in pyproject.toml
# This setup.py exists for backwards compatibility
if __name__ == "__main__":
    setup()
