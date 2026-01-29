"""
Plugin Management API Routes

REST endpoints for managing plugins, viewing plugin info, and configuring plugins
"""

from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
import logging

logger = logging.getLogger(__name__)

blp = Blueprint(
    "Plugins",
    "plugins",
    url_prefix="/api/plugins",
    description="Plugin management and configuration endpoints"
)


class PluginInfoSchema(Schema):
    """Schema for plugin information"""
    name = fields.Str(description="Plugin name")
    description = fields.Str(description="Plugin description")
    functions = fields.List(fields.Str(), description="Available functions")


class PluginListResponseSchema(Schema):
    """Schema for plugin list response"""
    plugins = fields.List(fields.Nested(PluginInfoSchema), description="List of registered plugins")
    count = fields.Int(description="Number of registered plugins")


class DeltaPositionSchema(Schema):
    """Schema for Delta ARM position"""
    x = fields.Float(description="X coordinate in mm")
    y = fields.Float(description="Y coordinate in mm")
    z = fields.Float(description="Z coordinate in mm")


class DeltaJointsSchema(Schema):
    """Schema for Delta ARM joint angles"""
    j1 = fields.Float(description="Joint 1 angle in degrees")
    j2 = fields.Float(description="Joint 2 angle in degrees")
    j3 = fields.Float(description="Joint 3 angle in degrees")


class DeltaStatusResponseSchema(Schema):
    """Schema for Delta ARM status response"""
    position = fields.Nested(DeltaPositionSchema, description="Current position")
    joints = fields.List(fields.Float(), description="Current joint angles")
    is_homed = fields.Bool(description="Homing status")
    speed = fields.Float(description="Current speed setting")
    acceleration = fields.Float(description="Current acceleration setting")
    gripper_state = fields.Str(description="Gripper state (open/closed)")


@blp.route("/")
class PluginList(MethodView):
    """
    List all registered plugins
    """
    
    @blp.response(200, PluginListResponseSchema)
    def get(self):
        """
        Get list of all registered plugins
        
        Returns information about all plugins currently registered
        with the interpreter, including their available functions.
        """
        from .interpreter import plugin_manager
        
        plugins = plugin_manager.list_plugins()
        
        return {
            'plugins': plugins,
            'count': len(plugins)
        }


@blp.route("/<string:plugin_name>")
class PluginDetail(MethodView):
    """
    Get detailed information about a specific plugin
    """
    
    @blp.response(200, PluginInfoSchema)
    def get(self, plugin_name):
        """
        Get detailed plugin information
        
        Returns detailed information about a specific plugin including
        its functions and current configuration.
        """
        from .interpreter import plugin_manager
        
        plugin = plugin_manager.get_plugin(plugin_name)
        
        if not plugin:
            return {'error': f'Plugin not found: {plugin_name}'}, 404
        
        return {
            'name': plugin.get_name(),
            'description': plugin.get_description(),
            'functions': list(plugin.get_functions().keys())
        }


@blp.route("/delta/status")
class DeltaStatus(MethodView):
    """
    Get Delta ARM plugin status
    """
    
    @blp.response(200, DeltaStatusResponseSchema)
    def get(self):
        """
        Get current Delta ARM status
        
        Returns current position, joint angles, speed settings,
        and gripper state of the Delta ARM.
        """
        from .interpreter import plugin_manager
        
        delta_plugin = plugin_manager.get_plugin('delta')
        
        if not delta_plugin:
            return {'error': 'Delta plugin not found'}, 404
        
        position = delta_plugin.get_position()
        joints = delta_plugin.get_joints()
        gripper = delta_plugin.gripper_state()
        
        return {
            'position': position,
            'joints': joints,
            'is_homed': delta_plugin.is_homed,
            'speed': delta_plugin.speed,
            'acceleration': delta_plugin.acceleration,
            'gripper_state': gripper['state']
        }


@blp.route("/delta/home")
class DeltaHome(MethodView):
    """
    Home the Delta ARM
    """
    
    @blp.response(200)
    def post(self):
        """
        Home the Delta ARM robot
        
        Moves the Delta ARM to its home position and sets the
        homing flag. This must be called before movement commands.
        """
        from .interpreter import plugin_manager
        
        delta_plugin = plugin_manager.get_plugin('delta')
        
        if not delta_plugin:
            return {'error': 'Delta plugin not found'}, 404
        
        result = delta_plugin.home()
        return result


@blp.route("/delta/move")
class DeltaMove(MethodView):
    """
    Move Delta ARM to position
    """
    
    @blp.arguments(DeltaPositionSchema)
    @blp.response(200)
    def post(self, data):
        """
        Move Delta ARM to cartesian coordinates
        
        Moves the Delta ARM end-effector to the specified
        cartesian coordinates (x, y, z) in millimeters.
        """
        from .interpreter import plugin_manager
        
        delta_plugin = plugin_manager.get_plugin('delta')
        
        if not delta_plugin:
            return {'error': 'Delta plugin not found'}, 404
        
        result = delta_plugin.moveto(data['x'], data['y'], data['z'])
        return result


@blp.route("/delta/movej")
class DeltaMoveJoints(MethodView):
    """
    Move Delta ARM joints
    """
    
    @blp.arguments(DeltaJointsSchema)
    @blp.response(200)
    def post(self, data):
        """
        Move Delta ARM joints to specified angles
        
        Moves the Delta ARM joints to the specified angles
        in degrees.
        """
        from .interpreter import plugin_manager
        
        delta_plugin = plugin_manager.get_plugin('delta')
        
        if not delta_plugin:
            return {'error': 'Delta plugin not found'}, 404
        
        result = delta_plugin.movej(data['j1'], data['j2'], data['j3'])
        return result


@blp.route("/delta/gripper/<string:action>")
class DeltaGripper(MethodView):
    """
    Control Delta ARM gripper
    """
    
    @blp.response(200)
    def post(self, action):
        """
        Open or close the Delta ARM gripper
        
        Controls the gripper state. Valid actions are 'open' and 'close'.
        """
        from .interpreter import plugin_manager
        
        delta_plugin = plugin_manager.get_plugin('delta')
        
        if not delta_plugin:
            return {'error': 'Delta plugin not found'}, 404
        
        if action == 'open':
            result = delta_plugin.gripper_open()
        elif action == 'close':
            result = delta_plugin.gripper_close()
        else:
            return {'error': f'Invalid action: {action}. Use "open" or "close"'}, 400
        
        return result
