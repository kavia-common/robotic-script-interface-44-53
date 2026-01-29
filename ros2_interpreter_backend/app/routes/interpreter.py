"""
Interpreter API Routes

REST endpoints for script execution, validation, and management
"""

from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
from ..interpreter.engine import LuaInterpreter, InterpreterContext, InterpreterError
from ..plugins.plugin_manager import PluginManager
from ..plugins.delta_plugin import DeltaArmPlugin
from ..ros2.ros2_bridge import ROS2Bridge
import logging

logger = logging.getLogger(__name__)

blp = Blueprint(
    "Interpreter",
    "interpreter",
    url_prefix="/api/interpreter",
    description="Script execution and interpreter management endpoints"
)

# Global instances
plugin_manager = PluginManager()
ros2_bridge = ROS2Bridge()

# Initialize Delta ARM plugin
delta_plugin = DeltaArmPlugin()
plugin_manager.register_plugin(delta_plugin)

# Initialize ROS2 bridge
ros2_bridge.initialize("interpreter_backend")


# Schemas
class ScriptExecuteSchema(Schema):
    """Schema for script execution request"""
    script = fields.Str(required=True, description="Lua-like script to execute")
    context = fields.Dict(keys=fields.Str(), values=fields.Raw(), description="Optional initial context variables")


class ScriptExecuteResponseSchema(Schema):
    """Schema for script execution response"""
    success = fields.Bool(description="Execution success status")
    output = fields.List(fields.Raw(), description="Script output")
    variables = fields.Dict(keys=fields.Str(), values=fields.Raw(), description="Final variable state")
    error = fields.Str(description="Error message if execution failed")


class ScriptValidateSchema(Schema):
    """Schema for script validation request"""
    script = fields.Str(required=True, description="Script to validate")


class ScriptValidateResponseSchema(Schema):
    """Schema for script validation response"""
    valid = fields.Bool(description="Validation result")
    errors = fields.List(fields.Str(), description="List of validation errors")
    warnings = fields.List(fields.Str(), description="List of validation warnings")


@blp.route("/execute")
class ScriptExecute(MethodView):
    """
    Execute a Lua-like script
    """
    
    @blp.arguments(ScriptExecuteSchema)
    @blp.response(200, ScriptExecuteResponseSchema)
    def post(self, data):
        """
        Execute a script and return results
        
        Executes the provided Lua-like script with access to Delta ARM
        plugin functions and ROS2 integration.
        """
        try:
            script = data['script']
            initial_context = data.get('context', {})
            
            # Create interpreter context
            context = InterpreterContext()
            
            # Add initial variables
            for key, value in initial_context.items():
                context.set_variable(key, value)
            
            # Register Delta plugin functions at root level (no prefix)
            # Also register with 'delta.' prefix for backward compatibility
            delta_plugin_obj = plugin_manager.get_plugin('delta')
            if delta_plugin_obj:
                delta_functions = delta_plugin_obj.get_functions()
                for func_name, func in delta_functions.items():
                    # Register at root level (e.g., MovP, ReadModbus)
                    context.register_function(func_name, func)
                    # Also register with 'delta.' prefix for backward compatibility
                    context.register_function(f'delta.{func_name}', func)
            
            # Register delta plugin instance for legacy dot notation
            context.register_plugin('delta', delta_plugin_obj)
            
            # Register other plugin functions (non-delta plugins keep their prefix)
            for func_name, func in plugin_manager.plugin_functions.items():
                if not func_name.startswith('delta.'):
                    context.register_function(func_name, func)
            
            # Create and execute interpreter
            interpreter = LuaInterpreter(context)
            result = interpreter.execute(script)
            
            logger.info("Script executed successfully")
            return {
                'success': True,
                'output': result['output'],
                'variables': result['variables']
            }
            
        except InterpreterError as e:
            logger.error(f"Interpreter error: {str(e)}")
            return {
                'success': False,
                'output': [],
                'variables': {},
                'error': str(e)
            }, 400
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'output': [],
                'variables': {},
                'error': f"Internal error: {str(e)}"
            }, 500


@blp.route("/validate")
class ScriptValidate(MethodView):
    """
    Validate a script without executing it
    """
    
    @blp.arguments(ScriptValidateSchema)
    @blp.response(200, ScriptValidateResponseSchema)
    def post(self, data):
        """
        Validate script syntax and structure
        
        Checks the script for syntax errors and potential issues
        without executing it.
        """
        try:
            script = data['script']
            errors = []
            warnings = []
            
            # Basic validation checks
            lines = script.strip().split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('--'):
                    continue
                
                # Check for basic syntax issues
                if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
                    if not line.count('=') >= 1:
                        errors.append(f"Line {i+1}: Invalid assignment syntax")
                
                # Check for unclosed parentheses
                if line.count('(') != line.count(')'):
                    errors.append(f"Line {i+1}: Unmatched parentheses")
                
                # Check for unclosed quotes
                if (line.count('"') % 2 != 0) or (line.count("'") % 2 != 0):
                    errors.append(f"Line {i+1}: Unclosed string literal")
            
            valid = len(errors) == 0
            
            return {
                'valid': valid,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': []
            }, 500


@blp.route("/context")
class InterpreterContextEndpoint(MethodView):
    """
    Get interpreter context information
    """
    
    @blp.response(200)
    def get(self):
        """
        Get available functions and plugin information
        
        Returns information about registered plugins and available
        functions that can be used in scripts.
        """
        plugins = plugin_manager.list_plugins()
        functions = list(plugin_manager.plugin_functions.keys())
        
        return {
            'plugins': plugins,
            'functions': functions,
            'ros2_initialized': ros2_bridge.is_initialized,
            'ros2_topics': ros2_bridge.get_topic_list(),
            'ros2_services': ros2_bridge.get_service_list()
        }
