"""
FuelTune Maps Module

This module provides comprehensive map editing functionality for FuelTech ECU
tuning tables including fuel, ignition, and boost maps with 2D/3D visualization,
versioning system, and FTManager integration.

Classes:
    MapEditor: Main map editing interface
    MapOperations: Map manipulation operations
    MapAlgorithms: Smoothing and interpolation algorithms
    MapVisualization: 3D visualization components
    MapSnapshots: Versioning and snapshot management
    FTManagerBridge: FTManager integration via clipboard

Functions:
    create_map_editor: Factory function for map editor instances
    load_map_from_file: Load map data from various formats
    export_map_to_ftmanager: Export map for FTManager compatibility

Author: FuelTune Development Team
Version: 1.0.0
"""

from .algorithms import MapAlgorithms
from .editor import MapEditor
from .ftmanager import FTManagerBridge
from .operations import MapOperations
from .snapshots import MapSnapshots
from .visualization import MapVisualization

__all__ = [
    "MapEditor",
    "MapOperations",
    "MapAlgorithms",
    "MapVisualization",
    "MapSnapshots",
    "FTManagerBridge",
]

__version__ = "1.0.0"
