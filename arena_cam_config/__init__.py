"""
Arena Camera Configuration GUI

A Textual-based interface for configuring ArenaSDK cameras with proper modal dialogs
and tree-based parameter editing.
"""

__version__ = "0.1.0"
__author__ = "Laurence"
__description__ = "Camera Configuration GUI using Textual for ArenaSDK cameras"

from .main import CameraConfigApp, main

__all__ = ["CameraConfigApp", "main"]
