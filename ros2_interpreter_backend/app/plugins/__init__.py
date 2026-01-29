"""
Plugins module

Provides plugin architecture for extending interpreter functionality.
"""

from .plugin_manager import Plugin, PluginManager
from .delta_plugin import DeltaArmPlugin

__all__ = ['Plugin', 'PluginManager', 'DeltaArmPlugin']
