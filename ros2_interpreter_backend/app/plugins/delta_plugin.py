"""
Delta ARM Plugin

Provides Delta robot arm control functions for the interpreter.
Conforms to Delta ARM API specification (DeltaAPI.txt).
"""

from typing import Dict, Any, List, Union, Optional
import logging
import math
import time
from .plugin_manager import Plugin

logger = logging.getLogger(__name__)


class DeltaArmPlugin(Plugin):
    """
    PUBLIC_INTERFACE
    Plugin for controlling Delta ARM robots
    
    Implements Delta ARM API specification including:
    - Movement control (MovP, MovL, MovJ)
    - Point management (SetGlobalPoint, ReadPoint)
    - Speed/acceleration control (SpdJ, AccJ, DecJ, SpdL, AccL, DecL)
    - Digital I/O (DI, DO, ExtDI, ExtDO)
    - Timing (WAIT, DELAY)
    - Modbus communication (ReadModbus, WriteModbus)
    - Accuracy control (Accur)
    """
    
    def __init__(self):
        """Initialize Delta ARM plugin"""
        # Current robot state
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': -200.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0}
        self.current_joints = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_homed = False
        
        # Speed and acceleration settings (percentage for joint, absolute for linear)
        self.speed_j = 10.0  # Joint speed in %
        self.acc_j = 10.0    # Joint acceleration in %
        self.dec_j = 10.0    # Joint deceleration in %
        
        self.speed_l = 100   # Linear speed in mm/sec
        self.acc_l = 10      # Linear acceleration in mm/sec²
        self.dec_l = 10      # Linear deceleration in mm/sec²
        
        # Accuracy mode
        self.accuracy_mode = "HIGH"
        
        # Point storage (1-1000)
        self.global_points = {}
        
        # Digital I/O state
        self.di_state = {i: False for i in range(1, 25)}  # DI pins 1-24
        self.do_state = {i: False for i in range(1, 13)}  # DO pins 1-12
        self.ext_di_state = {}  # External DI
        self.ext_do_state = {}  # External DO
        
        # Modbus registers
        self.modbus_registers = {}
        
        # User and tool frames
        self.current_uf = 0
        self.current_tf = 0
        
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
        return "Delta ARM robot control plugin conforming to Delta API specification"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the Delta ARM plugin
        
        Args:
            config: Configuration dictionary
                
        Returns:
            True if initialization successful
        """
        try:
            if 'workspace_limits' in config:
                self.workspace_limits = config['workspace_limits']
            
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
        Return available Delta ARM functions per Delta API specification
        """
        return {
            # Movement commands
            'MovP': self.MovP,
            'MovL': self.MovL,
            'MovJ': self.MovJ,
            
            # Speed and acceleration settings
            'SpdJ': self.SpdJ,
            'AccJ': self.AccJ,
            'DecJ': self.DecJ,
            'SpdL': self.SpdL,
            'AccL': self.AccL,
            'DecL': self.DecL,
            
            # Accuracy control
            'Accur': self.Accur,
            
            # Point management
            'SetGlobalPoint': self.SetGlobalPoint,
            'ReadPoint': self.ReadPoint,
            
            # Digital I/O
            'DI': self.DI,
            'DO': self.DO,
            'ExtDI': self.ExtDI,
            'ExtDO': self.ExtDO,
            
            # Timing
            'WAIT': self.WAIT,
            'DELAY': self.DELAY,
            
            # Modbus communication
            'ReadModbus': self.ReadModbus,
            'WriteModbus': self.WriteModbus,
            
            # Legacy compatibility (mapped to new functions)
            'home': self.home,
            'moveto': self.moveto_legacy,
            'movej': self.movej_legacy,
            'get_position': self.get_position,
            'get_joints': self.get_joints,
            'set_speed': self.set_speed_legacy,
            'set_acceleration': self.set_acceleration_legacy,
            'gripper_open': self.gripper_open,
            'gripper_close': self.gripper_close,
            'gripper_state': self.gripper_state,
            'move_relative': self.move_relative,
            'is_in_workspace': self.is_in_workspace,
        }
    
    # ===== Movement Commands (Delta API) =====
    
    def MovP(self, point: Union[int, str], **kwargs) -> Dict[str, Any]:
        """
        Point-to-point movement
        
        Args:
            point: Target point number (1-1000) or point name
            **kwargs: Optional parameters (SPD, ACC, DEC, X, Y, Z, RX, RY, RZ offsets)
            
        Returns:
            Status dictionary
        """
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed. Call home() first.'}
        
        # Get point data
        point_data = self._get_point_data(point)
        if point_data is None:
            return {'success': False, 'message': f'Point {point} not found'}
        
        # Apply offsets if provided
        target_pos = point_data.copy()
        if 'X' in kwargs:
            target_pos['x'] += kwargs['X']
        if 'Y' in kwargs:
            target_pos['y'] += kwargs['Y']
        if 'Z' in kwargs:
            target_pos['z'] += kwargs['Z']
        if 'RX' in kwargs:
            target_pos['rx'] += kwargs['RX']
        if 'RY' in kwargs:
            target_pos['ry'] += kwargs['RY']
        if 'RZ' in kwargs:
            target_pos['rz'] += kwargs['RZ']
        
        # Check workspace
        if not self.is_in_workspace(target_pos['x'], target_pos['y'], target_pos['z']):
            return {'success': False, 'message': 'Target position outside workspace'}
        
        # Use speed/acc settings from kwargs or defaults (speed can be overridden)
        # speed = kwargs.get('SPD', self.speed_j)  # Optional parameter for future use
        
        # Simulate movement
        self.current_position = target_pos
        self.current_joints = self._inverse_kinematics(
            target_pos['x'], target_pos['y'], target_pos['z']
        )
        
        logger.info(f"MovP to point {point}: {target_pos}")
        return {
            'success': True,
            'message': f'Moved to point {point}',
            'position': self.current_position.copy()
        }
    
    def MovL(self, point: Union[int, str], **kwargs) -> Dict[str, Any]:
        """
        Linear movement to point
        
        Args:
            point: Target point number or name
            **kwargs: Optional parameters (SPD, ACC, DEC, offsets)
            
        Returns:
            Status dictionary
        """
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed. Call home() first.'}
        
        # Get point data
        point_data = self._get_point_data(point)
        if point_data is None:
            return {'success': False, 'message': f'Point {point} not found'}
        
        # Apply offsets
        target_pos = point_data.copy()
        if 'X' in kwargs:
            target_pos['x'] += kwargs['X']
        if 'Y' in kwargs:
            target_pos['y'] += kwargs['Y']
        if 'Z' in kwargs:
            target_pos['z'] += kwargs['Z']
        
        # Check workspace
        if not self.is_in_workspace(target_pos['x'], target_pos['y'], target_pos['z']):
            return {'success': False, 'message': 'Target position outside workspace'}
        
        # Use linear speed settings (speed can be overridden)
        # speed = kwargs.get('SPD', self.speed_l)  # Optional parameter for future use
        
        # Simulate linear movement
        self.current_position = target_pos
        self.current_joints = self._inverse_kinematics(
            target_pos['x'], target_pos['y'], target_pos['z']
        )
        
        logger.info(f"MovL to point {point}: {target_pos}")
        return {
            'success': True,
            'message': f'Linear move to point {point}',
            'position': self.current_position.copy()
        }
    
    def MovJ(self, joint: int, degree: float, **kwargs) -> Dict[str, Any]:
        """
        Move single joint to specified angle
        
        Args:
            joint: Joint number (1-6)
            degree: Target angle in degrees (-360 to 360)
            **kwargs: Optional SPD, ACC, DEC parameters
            
        Returns:
            Status dictionary
        """
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed. Call home() first.'}
        
        if not 1 <= joint <= 6:
            return {'success': False, 'message': 'Joint number must be 1-6'}
        
        if not -360 <= degree <= 360:
            return {'success': False, 'message': 'Angle must be between -360 and 360 degrees'}
        
        # Update joint angle
        self.current_joints[joint - 1] = degree
        
        # Calculate new position (forward kinematics)
        self.current_position = self._forward_kinematics(*self.current_joints[:3])
        
        logger.info(f"MovJ: Joint {joint} to {degree} degrees")
        return {
            'success': True,
            'message': f'Joint {joint} moved to {degree} degrees',
            'joints': self.current_joints.copy()
        }
    
    # ===== Speed and Acceleration Control =====
    
    def SpdJ(self, speed: float) -> Dict[str, Any]:
        """
        Set joint maximum speed (percentage)
        
        Args:
            speed: Speed in % (0.001-100)
            
        Returns:
            Status dictionary
        """
        if not 0.001 <= speed <= 100:
            return {'success': False, 'message': 'Speed must be between 0.001 and 100%'}
        
        self.speed_j = speed
        logger.info(f"Joint speed set to {speed}%")
        return {'success': True, 'message': f'Joint speed set to {speed}%', 'speed': self.speed_j}
    
    def AccJ(self, acceleration: float) -> Dict[str, Any]:
        """
        Set joint acceleration (percentage)
        
        Args:
            acceleration: Acceleration in % (0.001-100)
            
        Returns:
            Status dictionary
        """
        if not 0.001 <= acceleration <= 100:
            return {'success': False, 'message': 'Acceleration must be between 0.001 and 100%'}
        
        self.acc_j = acceleration
        logger.info(f"Joint acceleration set to {acceleration}%")
        return {'success': True, 'message': f'Joint acceleration set to {acceleration}%'}
    
    def DecJ(self, deceleration: float) -> Dict[str, Any]:
        """
        Set joint deceleration (percentage)
        
        Args:
            deceleration: Deceleration in % (0.001-100)
            
        Returns:
            Status dictionary
        """
        if not 0.001 <= deceleration <= 100:
            return {'success': False, 'message': 'Deceleration must be between 0.001 and 100%'}
        
        self.dec_j = deceleration
        logger.info(f"Joint deceleration set to {deceleration}%")
        return {'success': True, 'message': f'Joint deceleration set to {deceleration}%'}
    
    def SpdL(self, speed: int) -> Dict[str, Any]:
        """
        Set linear maximum speed (mm/sec)
        
        Args:
            speed: Speed in mm/sec (1-2000)
            
        Returns:
            Status dictionary
        """
        if not 1 <= speed <= 2000:
            return {'success': False, 'message': 'Linear speed must be between 1 and 2000 mm/sec'}
        
        self.speed_l = speed
        logger.info(f"Linear speed set to {speed} mm/sec")
        return {'success': True, 'message': f'Linear speed set to {speed} mm/sec', 'speed': self.speed_l}
    
    def AccL(self, acceleration: int) -> Dict[str, Any]:
        """
        Set linear acceleration (mm/sec²)
        
        Args:
            acceleration: Acceleration in mm/sec² (1-25000)
            
        Returns:
            Status dictionary
        """
        if not 1 <= acceleration <= 25000:
            return {'success': False, 'message': 'Linear acceleration must be between 1 and 25000 mm/sec²'}
        
        self.acc_l = acceleration
        logger.info(f"Linear acceleration set to {acceleration} mm/sec²")
        return {'success': True, 'message': f'Linear acceleration set to {acceleration} mm/sec²'}
    
    def DecL(self, deceleration: int) -> Dict[str, Any]:
        """
        Set linear deceleration (mm/sec²)
        
        Args:
            deceleration: Deceleration in mm/sec² (1-25000)
            
        Returns:
            Status dictionary
        """
        if not 1 <= deceleration <= 25000:
            return {'success': False, 'message': 'Linear deceleration must be between 1 and 25000 mm/sec²'}
        
        self.dec_l = deceleration
        logger.info(f"Linear deceleration set to {deceleration} mm/sec²")
        return {'success': True, 'message': f'Linear deceleration set to {deceleration} mm/sec²'}
    
    # ===== Accuracy Control =====
    
    def Accur(self, mode: str, coord_type: str = "CART") -> Dict[str, Any]:
        """
        Set in-place accuracy mode
        
        Args:
            mode: Accuracy mode (HIGH, STANDARD, MEDIUM, ROUGH, MAXROUGH)
            coord_type: Coordinate type (default "CART")
            
        Returns:
            Status dictionary
        """
        valid_modes = ["HIGH", "STANDARD", "MEDIUM", "ROUGH", "MAXROUGH"]
        if mode not in valid_modes:
            return {'success': False, 'message': f'Mode must be one of {valid_modes}'}
        
        self.accuracy_mode = mode
        logger.info(f"Accuracy mode set to {mode}")
        return {'success': True, 'message': f'Accuracy set to {mode}', 'mode': self.accuracy_mode}
    
    # ===== Point Management =====
    
    def SetGlobalPoint(self, point_num: int, point_name: str, x: float, y: float, z: float,
                       *args, **kwargs) -> Dict[str, Any]:
        """
        Set global point data
        
        Args for Six-Axis:
            point_num: Point number (1-1000)
            point_name: Point name (must start with "GL_")
            x, y, z: Position coordinates in mm
            rx, ry, rz: Rotation angles in degrees
            elbow, shoulder, flip: Robot posture parameters
            uf, tf: User frame and tool frame (0-9)
            jrc: JRC table [J1-J7, JRC_Active]
            
        Returns:
            Status dictionary
        """
        if not 1 <= point_num <= 1000:
            return {'success': False, 'message': 'Point number must be between 1 and 1000'}
        
        if point_name and not point_name.startswith("GL_"):
            return {'success': False, 'message': 'Point name must start with "GL_"'}
        
        # Parse arguments based on robot type (assuming 6-axis)
        point_data = {
            'x': x, 'y': y, 'z': z,
            'rx': args[0] if len(args) > 0 else 0.0,
            'ry': args[1] if len(args) > 1 else 0.0,
            'rz': args[2] if len(args) > 2 else 0.0,
            'elbow': args[3] if len(args) > 3 else 0,
            'shoulder': args[4] if len(args) > 4 else 0,
            'flip': args[5] if len(args) > 5 else 0,
            'uf': args[6] if len(args) > 6 else 0,
            'tf': args[7] if len(args) > 7 else 0,
            'jrc': args[8] if len(args) > 8 else [0, 0, 0, 0, 0, 0, 0, 0],
            'name': point_name
        }
        
        self.global_points[point_num] = point_data
        if point_name:
            self.global_points[point_name] = point_data
        
        logger.info(f"SetGlobalPoint {point_num} ({point_name}): {point_data}")
        return {'success': True, 'message': f'Point {point_num} set successfully'}
    
    def ReadPoint(self, point: Union[int, str], item: str) -> Any:
        """
        Read point information
        
        Args:
            point: Point number or name
            item: Item to read (X, Y, Z, RX, RY, RZ, UF, TF, H, E, S, F, JRC)
            
        Returns:
            Requested item value or None if not found
        """
        point_data = self._get_point_data(point)
        if point_data is None:
            logger.error(f"Point {point} not found")
            return None
        
        item_map = {
            'X': 'x', 'Y': 'y', 'Z': 'z',
            'RX': 'rx', 'RY': 'ry', 'RZ': 'rz',
            'UF': 'uf', 'TF': 'tf',
            'H': 'hand', 'E': 'elbow', 'S': 'shoulder', 'F': 'flip',
            'JRC': 'jrc'
        }
        
        key = item_map.get(item.upper())
        if key and key in point_data:
            return point_data[key]
        
        return None
    
    # ===== Digital I/O =====
    
    def DI(self, pin_index: Union[int, str], length: Optional[int] = None) -> Union[str, int]:
        """
        Read digital input
        
        Args:
            pin_index: Pin number (1-24) or pin name
            length: Optional, number of pins to read (1-24)
            
        Returns:
            "ON"/"OFF" for single pin, or decimal status for multiple pins
        """
        if length is None:
            # Single pin read
            pin = self._resolve_pin_index(pin_index)
            if not 1 <= pin <= 24:
                return "OFF"
            return "ON" if self.di_state.get(pin, False) else "OFF"
        else:
            # Multiple pin read
            pin = self._resolve_pin_index(pin_index)
            status_num = 0
            for i in range(length):
                if self.di_state.get(pin + i, False):
                    status_num |= (1 << i)
            return status_num
    
    def DO(self, pin_index: Union[int, str], *args) -> Dict[str, Any]:
        """
        Set digital output
        
        Syntax variants:
            DO(pin, status)
            DO(pin, status, delay_time)
            DO(pin, length, status_num)
            DO(pin, length, status_num, delay_time)
        
        Args:
            pin_index: Pin number (1-12) or name
            *args: Variable arguments based on syntax
            
        Returns:
            Status dictionary
        """
        pin = self._resolve_pin_index(pin_index)
        
        if len(args) == 1:
            # DO(pin, status)
            status = args[0]
            self._set_do_pin(pin, status)
            return {'success': True, 'message': f'DO {pin} set to {status}'}
        
        elif len(args) == 2:
            if isinstance(args[0], str):
                # DO(pin, status, delay_time)
                status, delay = args
                self._set_do_pin(pin, status)
                time.sleep(delay)
                # Reverse signal after delay
                self._set_do_pin(pin, "OFF" if status == "ON" else "ON")
                return {'success': True, 'message': f'DO {pin} toggled with {delay}s delay'}
            else:
                # DO(pin, length, status_num)
                length, status_num = args
                for i in range(length):
                    state = "ON" if (status_num & (1 << i)) else "OFF"
                    self._set_do_pin(pin + i, state)
                return {'success': True, 'message': f'{length} DO pins set'}
        
        elif len(args) == 3:
            # DO(pin, length, status_num, delay_time)
            length, status_num, delay = args
            for i in range(length):
                state = "ON" if (status_num & (1 << i)) else "OFF"
                self._set_do_pin(pin + i, state)
            return {'success': True, 'message': f'{length} DO pins set with delay'}
        
        return {'success': False, 'message': 'Invalid DO arguments'}
    
    def ExtDI(self, address_index: int, pin_index: int) -> str:
        """
        Read external board digital input
        
        Args:
            address_index: External board station number
            pin_index: Pin number on external board
            
        Returns:
            "ON" or "OFF"
        """
        key = (address_index, pin_index)
        return "ON" if self.ext_di_state.get(key, False) else "OFF"
    
    def ExtDO(self, address_index: int, pin_index: int, status: str, 
              delay_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Set external board digital output
        
        Args:
            address_index: External board station number
            pin_index: Pin number
            status: "ON" or "OFF"
            delay_time: Optional delay in seconds
            
        Returns:
            Status dictionary
        """
        key = (address_index, pin_index)
        self.ext_do_state[key] = (status == "ON")
        
        if delay_time:
            time.sleep(delay_time)
            # Reverse signal
            self.ext_do_state[key] = not self.ext_do_state[key]
        
        return {'success': True, 'message': f'ExtDO {address_index}:{pin_index} set to {status}'}
    
    # ===== Timing Functions =====
    
    def WAIT(self, *args) -> Dict[str, Any]:
        """
        Wait for condition or timeout
        
        Syntax variants:
            WAIT(io_type, io_index, status, timeout)
            WAIT(modbus_var, modbus_addr, data_type, data)
        
        Args:
            *args: Variable arguments
            
        Returns:
            Status dictionary
        """
        if len(args) >= 3 and isinstance(args[0], str) and args[0] in ["DI", "DO"]:
            # Wait for DI/DO
            io_type, io_index, status = args[0], args[1], args[2]
            timeout = args[3] if len(args) > 3 else None
            
            start_time = time.time()
            while True:
                if io_type == "DI":
                    current_status = self.DI(io_index)
                else:
                    pin = self._resolve_pin_index(io_index)
                    current_status = "ON" if self.do_state.get(pin, False) else "OFF"
                
                if current_status == status:
                    return {'success': True, 'message': f'Condition met: {io_type} {io_index} is {status}'}
                
                if timeout and (time.time() - start_time) * 1000 > timeout:
                    return {'success': True, 'message': 'Timeout reached', 'timeout': True}
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
        
        return {'success': False, 'message': 'Invalid WAIT arguments'}
    
    def DELAY(self, delay_time: float) -> Dict[str, Any]:
        """
        Delay execution
        
        Args:
            delay_time: Delay time in seconds (minimum 0.001)
            
        Returns:
            Status dictionary
        """
        if delay_time < 0.001:
            return {'success': False, 'message': 'Delay time must be at least 0.001 seconds'}
        
        time.sleep(delay_time)
        return {'success': True, 'message': f'Delayed {delay_time} seconds'}
    
    # ===== Modbus Communication =====
    
    def ReadModbus(self, reg_address: int, size: str) -> Optional[int]:
        """
        Read Modbus register
        
        Args:
            reg_address: Register address (0x1000-0x1FFF, 0x3000-0x3FFF)
            size: "W" (16-bit) or "DW" (32-bit)
            
        Returns:
            Register value or None
        """
        if size == "DW" and reg_address % 2 != 0:
            logger.error("DW address must be even")
            return None
        
        return self.modbus_registers.get((reg_address, size), 0)
    
    def WriteModbus(self, reg_address: int, size: str, value: int) -> Dict[str, Any]:
        """
        Write Modbus register
        
        Args:
            reg_address: Register address
            size: "W" or "DW"
            value: Value to write
            
        Returns:
            Status dictionary
        """
        if size == "DW" and reg_address % 2 != 0:
            return {'success': False, 'message': 'DW address must be even'}
        
        # Validate value range
        if size == "W" and not -32767 <= value <= 32767:
            return {'success': False, 'message': 'W value must be -32767 to 32767'}
        if size == "DW" and not -2147483648 <= value <= 2147483647:
            return {'success': False, 'message': 'DW value must be -2147483648 to 2147483647'}
        
        self.modbus_registers[(reg_address, size)] = value
        return {'success': True, 'message': f'Modbus {size} at {hex(reg_address)} set to {value}'}
    
    # ===== Legacy Compatibility Functions =====
    
    def home(self) -> Dict[str, Any]:
        """Legacy home function - sets robot to home position"""
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': -200.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0}
        self.current_joints = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_homed = True
        logger.info("Robot homed (legacy function)")
        return {'success': True, 'message': 'Robot homed', 'position': self.current_position.copy()}
    
    def moveto_legacy(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """Legacy moveto function - maps to cartesian movement"""
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed'}
        
        if not self.is_in_workspace(x, y, z):
            return {'success': False, 'message': 'Position outside workspace'}
        
        self.current_position.update({'x': x, 'y': y, 'z': z})
        self.current_joints = self._inverse_kinematics(x, y, z)
        
        return {'success': True, 'message': f'Moved to ({x}, {y}, {z})', 'position': self.current_position.copy()}
    
    def movej_legacy(self, j1: float, j2: float, j3: float) -> Dict[str, Any]:
        """Legacy movej function"""
        if not self.is_homed:
            return {'success': False, 'message': 'Robot not homed'}
        
        self.current_joints[:3] = [j1, j2, j3]
        self.current_position = self._forward_kinematics(j1, j2, j3)
        
        return {'success': True, 'message': f'Joints moved to ({j1}, {j2}, {j3})'}
    
    def get_position(self) -> Dict[str, float]:
        """Get current position"""
        return self.current_position.copy()
    
    def get_joints(self) -> List[float]:
        """Get current joint angles"""
        return self.current_joints.copy()
    
    def set_speed_legacy(self, speed: float) -> Dict[str, Any]:
        """Legacy speed setting - maps to SpdL"""
        return self.SpdL(int(speed))
    
    def set_acceleration_legacy(self, accel: float) -> Dict[str, Any]:
        """Legacy acceleration setting - maps to AccL"""
        return self.AccL(int(accel))
    
    def move_relative(self, dx: float, dy: float, dz: float) -> Dict[str, Any]:
        """Move relative to current position"""
        new_x = self.current_position['x'] + dx
        new_y = self.current_position['y'] + dy
        new_z = self.current_position['z'] + dz
        return self.moveto_legacy(new_x, new_y, new_z)
    
    def is_in_workspace(self, x: float, y: float, z: float) -> bool:
        """Check if position is within workspace"""
        return (
            self.workspace_limits['x'][0] <= x <= self.workspace_limits['x'][1] and
            self.workspace_limits['y'][0] <= y <= self.workspace_limits['y'][1] and
            self.workspace_limits['z'][0] <= z <= self.workspace_limits['z'][1]
        )
    
    # Gripper functions (not in spec but maintained for compatibility)
    def gripper_open(self) -> Dict[str, Any]:
        """Open gripper (compatibility)"""
        return self.DO(1, "OFF")
    
    def gripper_close(self) -> Dict[str, Any]:
        """Close gripper (compatibility)"""
        return self.DO(1, "ON")
    
    def gripper_state(self) -> Dict[str, Any]:
        """Get gripper state (compatibility)"""
        state = self.DI(1)
        return {'state': 'closed' if state == "ON" else 'open', 'is_closed': state == "ON"}
    
    # ===== Helper Methods =====
    
    def _get_point_data(self, point: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get point data by number or name"""
        return self.global_points.get(point)
    
    def _resolve_pin_index(self, pin_index: Union[int, str]) -> int:
        """Resolve pin index from number or name"""
        if isinstance(pin_index, int):
            return pin_index
        # In real implementation, would look up pin name
        return 1
    
    def _set_do_pin(self, pin: int, status: str):
        """Set DO pin state"""
        if 1 <= pin <= 12:
            self.do_state[pin] = (status == "ON")
    
    def _inverse_kinematics(self, x: float, y: float, z: float) -> List[float]:
        """Simplified inverse kinematics"""
        angle = math.degrees(math.atan2(y, x))
        radius = math.sqrt(x**2 + y**2)
        z_angle = math.degrees(math.atan2(abs(z), radius)) if radius > 0 else 0
        return [angle, z_angle, z_angle, 0.0, 0.0, 0.0]
    
    def _forward_kinematics(self, j1: float, j2: float, j3: float) -> Dict[str, float]:
        """Simplified forward kinematics"""
        avg_angle = (j2 + j3) / 2
        radius = 100 * math.cos(math.radians(avg_angle))
        z = -200 * math.sin(math.radians(avg_angle))
        x = radius * math.cos(math.radians(j1))
        y = radius * math.sin(math.radians(j1))
        return {'x': x, 'y': y, 'z': z, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0}
