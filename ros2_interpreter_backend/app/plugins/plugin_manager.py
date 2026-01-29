"""
Plugin Manager for Delta ARM and other robotic plugins

This module provides the plugin architecture for extending the interpreter
with custom functionality, particularly for Delta ARM robot control.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """
    Abstract base class for interpreter plugins
    All plugins must inherit from this class
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name"""
        pass
    
    @abstractmethod
    def get_functions(self) -> Dict[str, callable]:
        """
        Return a dictionary of function names to callable objects
        These functions will be available in the interpreter
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up plugin resources"""
        pass
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "No description provided"


class PluginManager:
    """
    PUBLIC_INTERFACE
    Manages plugin lifecycle and registration
    """
    
    def __init__(self):
        """Initialize the plugin manager"""
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_functions: Dict[str, callable] = {}
        
    def register_plugin(self, plugin: Plugin, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        PUBLIC_INTERFACE
        Register a new plugin
        
        Args:
            plugin: Plugin instance to register
            config: Optional configuration dictionary
            
        Returns:
            True if registration successful
            
        Raises:
            ValueError: If plugin with same name already registered
        """
        plugin_name = plugin.get_name()
        
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered")
        
        # Initialize plugin
        init_config = config or {}
        if not plugin.initialize(init_config):
            logger.error(f"Failed to initialize plugin: {plugin_name}")
            return False
        
        # Register plugin
        self.plugins[plugin_name] = plugin
        
        # Register plugin functions
        functions = plugin.get_functions()
        for func_name, func in functions.items():
            full_name = f"{plugin_name}.{func_name}"
            self.plugin_functions[full_name] = func
            logger.info(f"Registered function: {full_name}")
        
        logger.info(f"Successfully registered plugin: {plugin_name}")
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        PUBLIC_INTERFACE
        Unregister a plugin and clean up its resources
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration successful
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Remove plugin functions
        functions_to_remove = [name for name in self.plugin_functions if name.startswith(f"{plugin_name}.")]
        for func_name in functions_to_remove:
            del self.plugin_functions[func_name]
        
        # Cleanup and remove plugin
        plugin.cleanup()
        del self.plugins[plugin_name]
        
        logger.info(f"Unregistered plugin: {plugin_name}")
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        PUBLIC_INTERFACE
        Get a registered plugin by name
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """
        PUBLIC_INTERFACE
        Get list of all registered plugins
        
        Returns:
            List of dictionaries with plugin information
        """
        return [
            {
                'name': name,
                'description': plugin.get_description(),
                'functions': list(plugin.get_functions().keys())
            }
            for name, plugin in self.plugins.items()
        ]
    
    def get_function(self, function_name: str) -> Optional[callable]:
        """
        PUBLIC_INTERFACE
        Get a plugin function by its full name (plugin.function)
        
        Args:
            function_name: Full function name (e.g., "delta.moveto")
            
        Returns:
            Callable function or None if not found
        """
        return self.plugin_functions.get(function_name)
    
    def call_function(self, function_name: str, *args, **kwargs) -> Any:
        """
        PUBLIC_INTERFACE
        Call a plugin function by name
        
        Args:
            function_name: Full function name (e.g., "delta.moveto")
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ValueError: If function not found
        """
        func = self.get_function(function_name)
        if func is None:
            raise ValueError(f"Function not found: {function_name}")
        
        return func(*args, **kwargs)
    
    def cleanup_all(self):
        """
        PUBLIC_INTERFACE
        Cleanup all registered plugins
        """
        for plugin_name in list(self.plugins.keys()):
            self.unregister_plugin(plugin_name)
