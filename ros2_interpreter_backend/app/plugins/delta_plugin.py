"""
Delta ARM Plugin

Provides Delta robot arm control functions for the interpreter.
Based on standard Delta robot kinematics and control patterns.
"""

from typing import Dict, Any, List
import logging
import math
from .plugin_manager import Plugin

logger = logging.getLogger(__name__)


class DeltaArmPlugin(Plugin):
    """
    PUBLIC_INTERFACE
    Plugin for controlling Delta ARM robots
    
    Provides functions for:
    - Movement control (cartesian and joint space)
    - Gripper/end-effector control
    - Position querying
    - Homing and calibration
    - Speed and acceleration control
    """
    
    def __init__(self):
        """Initialize Delta ARM plugin"""
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': -200.0}
        self.current_joints = [0.0, 0.0, 0.0]
        self.gripper_state = False
        self.speed = 100  # mm/s
        self.acceleration = 500  # mm/s²
        self.is_homed = False
        self.workspace_limits = {
            'x': (-150, 150),
            'y': (-150, 150),
            'z': (-300, -100)
        }
        
    def get_name(self) -> str:
        """Return plugin name"""
        return "delta"
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "Delta ARM robot control plugin with movement, gripper, and configuration functions"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the Delta ARM plugin
        
        Args:
            config: Configuration dictionary with optional parameters:
                - workspace_limits: Custom workspace limits
                - default_speed: Default movement speed
                - default_acceleration: Default acceleration
                
        Returns:
            True if initialization successful
        """
        try:
            if 'workspace_limits' in config:
                self.workspace_limits = config['workspace_limits']
            
            if 'default_speed' in config:
                self.speed = config['default_speed']
            
            if 'default_acceleration' in config:
                self.acceleration = config['default_acceleration']
            
            logger.info("Delta ARM plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Delta ARM plugin: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up Delta ARM resources"""
        logger.info("Delta ARM plugin cleaned up")
    
    def get_functions(self) -> Dict[str, callable]:
        """
        Return available Delta ARM functions
        
        Functions:
            - moveto(x, y, z): Move to cartesian coordinates
            - movej(j1, j2, j3): Move joints to specified angles
            - home(): Home the robot
            - get_position(): Get current cartesian position
            - get_joints(): Get current joint angles
            - set_speed(speed): Set movement speed
            - set_acceleration(accel): Set acceleration
            - gripper_open(): Open gripper
            - gripper_close(): Close gripper
            - gripper_state(): Get gripper state
            - move_relative(dx, dy, dz): Move relative to current position
            - is_in_workspace(x, y, z): Check if position is valid
        """
        return {
            'moveto': self.moveto,
            'movej': self.movej,
            'home': self.home,
            'get_position': self.get_position,
            'get_joints': self.get_joints,
            'set_speed': self.set_speed,
            'set_acceleration': self.set_acceleration,
            'gripper_open': self.gripper_open,
            'gripper_close': self.gripper_close,
            'gripper_state': self.gripper_state,
            'move_relative': self.move_relative,
            'is_in_workspace': self.is_in_workspace,
        }
    
    # Movement Functions
    
    def moveto(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """
        Move to cartesian coordinates
        
        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            z: Z coordinate in mm (negative, below base)
            
        Returns:
            Status dictionary with success flag and message
        """
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed. Call home() first.'}
        
        if not self.is_in_workspace(x, y, z):
            return {'success': False, 'message': 'Target position outside workspace'}
        
        # Simulate movement
        self.current_position = {'x': x, 'y': y, 'z': z}
        
        # Calculate joint angles (simplified inverse kinematics)
        self.current_joints = self._inverse_kinematics(x, y, z)
        
        logger.info(f"Moved to position: ({x}, {y}, {z})")
        return {
            'success': True,
            'message': f'Moved to ({x}, {y}, {z})',
            'position': self.current_position.copy()
        }
    
    def movej(self, j1: float, j2: float, j3: float) -> Dict[str, Any]:
        """
        Move joints to specified angles
        
        Args:
            j1: Joint 1 angle in degrees
            j2: Joint 2 angle in degrees
            j3: Joint 3 angle in degrees
            
        Returns:
            Status dictionary
        """
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed. Call home() first.'}
        
        # Validate joint limits
        if not all(-120 <= j <= 120 for j in [j1, j2, j3]):
            return {'success': False, 'message': 'Joint angles outside limits (-120 to 120 degrees)'}
        
        self.current_joints = [j1, j2, j3]
        
        # Calculate cartesian position (simplified forward kinematics)
        self.current_position = self._forward_kinematics(j1, j2, j3)
        
        logger.info(f"Moved joints to: ({j1}, {j2}, {j3})")
        return {
            'success': True,
            'message': f'Moved joints to ({j1}, {j2}, {j3})',
            'joints': self.current_joints.copy()
        }
    
    def move_relative(self, dx: float, dy: float, dz: float) -> Dict[str, Any]:
        """
        Move relative to current position
        
        Args:
            dx: X displacement in mm
            dy: Y displacement in mm
            dz: Z displacement in mm
            
        Returns:
            Status dictionary
        """
        new_x = self.current_position['x'] + dx
        new_y = self.current_position['y'] + dy
        new_z = self.current_position['z'] + dz
        
        return self.moveto(new_x, new_y, new_z)
    
    def home(self) -> Dict[str, Any]:
        """
        Home the robot to its home position
        
        Returns:
            Status dictionary
        """
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': -200.0}
        self.current_joints = [0.0, 0.0, 0.0]
        self.is_homed = True
        
        logger.info("Robot homed successfully")
        return {
            'success': True,
            'message': 'Robot homed',
            'position': self.current_position.copy()
        }
    
    # Query Functions
    
    def get_position(self) -> Dict[str, float]:
        """
        Get current cartesian position
        
        Returns:
            Dictionary with x, y, z coordinates
        """
        return self.current_position.copy()
    
    def get_joints(self) -> List[float]:
        """
        Get current joint angles
        
        Returns:
            List of joint angles [j1, j2, j3]
        """
        return self.current_joints.copy()
    
    def is_in_workspace(self, x: float, y: float, z: float) -> bool:
        """
        Check if position is within workspace limits
        
        Args:
            x, y, z: Position coordinates
            
        Returns:
            True if position is valid
        """
        return (
            self.workspace_limits['x'][0] <= x <= self.workspace_limits['x'][1] and
            self.workspace_limits['y'][0] <= y <= self.workspace_limits['y'][1] and
            self.workspace_limits['z'][0] <= z <= self.workspace_limits['z'][1]
        )
    
    # Configuration Functions
    
    def set_speed(self, speed: float) -> Dict[str, Any]:
        """
        Set movement speed
        
        Args:
            speed: Speed in mm/s (1-500)
            
        Returns:
            Status dictionary
        """
        if not 1 <= speed <= 500:
            return {'success': False, 'message': 'Speed must be between 1 and 500 mm/s'}
        
        self.speed = speed
        logger.info(f"Speed set to {speed} mm/s")
        return {'success': True, 'message': f'Speed set to {speed} mm/s', 'speed': self.speed}
    
    def set_acceleration(self, accel: float) -> Dict[str, Any]:
        """
        Set acceleration
        
        Args:
            accel: Acceleration in mm/s² (1-2000)
            
        Returns:
            Status dictionary
        """
        if not 1 <= accel <= 2000:
            return {'success': False, 'message': 'Acceleration must be between 1 and 2000 mm/s²'}
        
        self.acceleration = accel
        logger.info(f"Acceleration set to {accel} mm/s²")
        return {'success': True, 'message': f'Acceleration set to {accel} mm/s²', 'acceleration': self.acceleration}
    
    # Gripper Functions
    
    def gripper_open(self) -> Dict[str, Any]:
        """
        Open the gripper
        
        Returns:
            Status dictionary
        """
        self.gripper_state = False
        logger.info("Gripper opened")
        return {'success': True, 'message': 'Gripper opened', 'state': 'open'}
    
    def gripper_close(self) -> Dict[str, Any]:
        """
        Close the gripper
        
        Returns:
            Status dictionary
        """
        self.gripper_state = True
        logger.info("Gripper closed")
        return {'success': True, 'message': 'Gripper closed', 'state': 'closed'}
    
    def gripper_state(self) -> Dict[str, Any]:
        """
        Get gripper state
        
        Returns:
            Dictionary with gripper state
        """
        state = 'closed' if self.gripper_state else 'open'
        return {'state': state, 'is_closed': self.gripper_state}
    
    # Internal helper methods
    
    def _inverse_kinematics(self, x: float, y: float, z: float) -> List[float]:
        """
        Simplified inverse kinematics calculation
        Real implementation would use Delta robot IK equations
        """
        # Simplified: use angular position based on cartesian coords
        angle = math.degrees(math.atan2(y, x))
        radius = math.sqrt(x**2 + y**2)
        z_angle = math.degrees(math.atan2(abs(z), radius))
        
        return [angle, z_angle, z_angle]
    
    def _forward_kinematics(self, j1: float, j2: float, j3: float) -> Dict[str, float]:
        """
        Simplified forward kinematics calculation
        Real implementation would use Delta robot FK equations
        """
        # Simplified: convert joint angles to approximate cartesian position
        avg_angle = (j2 + j3) / 2
        radius = 100 * math.cos(math.radians(avg_angle))
        z = -200 * math.sin(math.radians(avg_angle))
        
        x = radius * math.cos(math.radians(j1))
        y = radius * math.sin(math.radians(j1))
        
        return {'x': x, 'y': y, 'z': z}
