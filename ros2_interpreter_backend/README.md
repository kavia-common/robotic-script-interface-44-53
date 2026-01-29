# ROS2 Interpreter Backend

A Lua-like interpreter built on Flask with plugin support for Delta ARM APIs and ROS2 integration for robotic communication.

## Features

- **Lua-like Scripting**: Execute scripts with Lua-inspired syntax
- **Delta ARM Plugin**: Control Delta robots with comprehensive APIs conforming to Delta specification
- **ROS2 Integration**: Publish/subscribe to topics and call services
- **Plugin Architecture**: Extensible plugin system for custom functionality
- **REST API**: Complete REST API for script execution and robot control
- **Real-time Communication**: WebSocket support for ROS2 messaging

## Architecture

### Components

1. **Interpreter Engine** (`app/interpreter/engine.py`)
   - Parses and executes Lua-like scripts
   - Supports variables, functions, and control structures
   - Extensible with plugin functions

2. **Plugin Manager** (`app/plugins/plugin_manager.py`)
   - Manages plugin lifecycle
   - Registers plugin functions with interpreter
   - Provides plugin discovery and configuration

3. **Delta ARM Plugin** (`app/plugins/delta_plugin.py`)
   - Implements Delta ARM API specification
   - Movement control (MovP, MovL, MovJ)
   - Point management (SetGlobalPoint, ReadPoint)
   - Speed/acceleration control (SpdJ, AccJ, DecJ, SpdL, AccL, DecL)
   - Digital I/O (DI, DO, ExtDI, ExtDO)
   - Timing functions (WAIT, DELAY)
   - Modbus communication (ReadModbus, WriteModbus)
   - Accuracy control (Accur)

4. **ROS2 Bridge** (`app/ros2/ros2_bridge.py`)
   - Topic publishing and subscribing
   - Service calls
   - Message history
   - Node management

## API Endpoints

### Interpreter Endpoints

- `POST /api/interpreter/execute` - Execute a script
- `POST /api/interpreter/validate` - Validate script syntax
- `GET /api/interpreter/context` - Get available functions and plugins

### Plugin Endpoints

- `GET /api/plugins/` - List all registered plugins
- `GET /api/plugins/{name}` - Get plugin details
- `GET /api/plugins/delta/status` - Get Delta ARM status
- `POST /api/plugins/delta/home` - Home Delta ARM
- `POST /api/plugins/delta/move` - Move to position
- `POST /api/plugins/delta/movej` - Move joints
- `POST /api/plugins/delta/gripper/{action}` - Control gripper

### ROS2 Endpoints

- `GET /api/ros2/status` - Get ROS2 bridge status
- `POST /api/ros2/publish` - Publish to topic
- `GET /api/ros2/topics` - List active topics
- `GET /api/ros2/services` - List available services
- `POST /api/ros2/call` - Call ROS2 service
- `GET /api/ros2/messages` - Get message history

## Script Syntax - Delta API Specification

### Movement Commands

```lua
-- Set global points (Six-axis robot)
-- SetGlobalPoint(point_num, name, x, y, z, rx, ry, rz, elbow, shoulder, flip, uf, tf, jrc)
delta.SetGlobalPoint(1, "GL_P1", 100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Point-to-point movement
delta.MovP(1)  -- Move to point 1
delta.MovP("GL_P1")  -- Move to point by name

-- Linear movement
delta.MovL(1)  -- Linear move to point 1

-- Move single joint
delta.MovJ(1, 45.0)  -- Move joint 1 to 45 degrees
```

### Speed and Acceleration Control

```lua
-- Joint speed/acceleration (percentage)
delta.SpdJ(50)   -- Set joint speed to 50%
delta.AccJ(50)   -- Set joint acceleration to 50%
delta.DecJ(50)   -- Set joint deceleration to 50%

-- Linear speed/acceleration (mm/sec, mm/sec²)
delta.SpdL(150)   -- Set linear speed to 150 mm/sec
delta.AccL(500)   -- Set linear acceleration to 500 mm/sec²
delta.DecL(500)   -- Set linear deceleration to 500 mm/sec²
```

### Accuracy Control

```lua
-- Set in-place accuracy mode
delta.Accur("HIGH", "CART")      -- Highest accuracy
delta.Accur("STANDARD", "CART")  -- Standard accuracy
delta.Accur("MEDIUM", "CART")    -- Medium accuracy
delta.Accur("ROUGH", "CART")     -- Rough accuracy
delta.Accur("MAXROUGH", "CART")  -- Maximum rough accuracy
```

### Point Management

```lua
-- Read point information
x_coord = delta.ReadPoint(1, "X")     -- Read X coordinate of point 1
y_coord = delta.ReadPoint("GL_P1", "Y")  -- Read Y by point name
uf = delta.ReadPoint(1, "UF")         -- Read user frame
```

### Digital I/O

```lua
-- Digital input
status = delta.DI(1)           -- Read DI pin 1 (returns "ON" or "OFF")
status_num = delta.DI(1, 4)    -- Read 4 consecutive DI pins (returns decimal)

-- Digital output
delta.DO(1, "ON")              -- Set DO pin 1 to ON
delta.DO(1, "ON", 2.0)         -- Set DO 1 to ON for 2 seconds, then toggle
delta.DO(1, 4, 5)              -- Set multiple DO pins (binary 0101)

-- External board I/O
status = delta.ExtDI(4, 1)     -- Read DI pin 1 on external board station 4
delta.ExtDO(4, 1, "ON")        -- Set DO pin 1 on external board station 4
```

### Timing Functions

```lua
-- Delay execution
delta.DELAY(0.5)               -- Delay 0.5 seconds
delta.DELAY(2.0)               -- Delay 2 seconds

-- Wait for condition
delta.WAIT("DI", 1, "ON")                    -- Wait for DI 1 to be ON
delta.WAIT("DI", 1, "ON", 1000)             -- Wait with 1000ms timeout
delta.WAIT("DO", 2, "OFF")                   -- Wait for DO 2 to be OFF
```

### Modbus Communication

```lua
-- Read Modbus register
value = delta.ReadModbus(0x1000, "W")   -- Read 16-bit register
value = delta.ReadModbus(0x1000, "DW")  -- Read 32-bit register

-- Write Modbus register
delta.WriteModbus(0x1000, "W", 100)     -- Write 16-bit value
delta.WriteModbus(0x1002, "DW", 50000)  -- Write 32-bit value
```

### Legacy Compatibility Functions

```lua
-- These functions are maintained for backward compatibility
delta.home()                           -- Home the robot
delta.moveto(100, 50, -200)           -- Move to cartesian coordinates
delta.movej(0, 45, 45)                -- Move joints
delta.move_relative(10, 0, -5)        -- Move relative
delta.get_position()                  -- Get current position
delta.get_joints()                    -- Get current joint angles
delta.set_speed(150)                  -- Set speed (maps to SpdL)
delta.set_acceleration(600)           -- Set acceleration (maps to AccL)
delta.gripper_open()                  -- Open gripper
delta.gripper_close()                 -- Close gripper
delta.is_in_workspace(100, 50, -200)  -- Check workspace validity
```

## Example Scripts

### Simple Movement with Delta API

```lua
-- Home the robot
delta.home()

-- Set points
delta.SetGlobalPoint(1, "GL_P1", 100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(2, "GL_P2", 0, 100, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Set speed
delta.SpdJ(50)

-- Move to points
delta.MovP(1)
delta.MovP(2)
```

### Pick and Place with I/O

```lua
-- Home robot
delta.home()

-- Configure speeds
delta.SpdL(150)
delta.AccL(500)

-- Set points
delta.SetGlobalPoint(10, "GL_Pick", 80, 80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(11, "GL_Place", -80, -80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Open gripper
delta.DO(1, "OFF")

-- Move to pick
delta.MovL(10)

-- Close gripper
delta.DO(1, "ON")
delta.DELAY(0.5)

-- Move to place
delta.MovL(11)

-- Release
delta.DO(1, "OFF")
delta.DELAY(0.5)

-- Home
delta.home()
```

### Speed Control Example

```lua
-- Home robot
delta.home()

-- Set points
delta.SetGlobalPoint(1, "GL_P1", 100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(2, "GL_P2", 0, 100, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Fast movement
delta.SpdJ(80)
delta.MovP(1)

-- Slow movement
delta.SpdJ(20)
delta.MovP(2)

-- Return to normal speed
delta.SpdJ(50)
delta.home()
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

## Configuration

The application can be configured through environment variables:

- `FLASK_ENV` - Environment (development/production)
- `FLASK_PORT` - Port to run on (default: 5000)
- `ROS2_NODE_NAME` - Custom ROS2 node name

## Development

### Adding New Plugins

1. Create a new plugin class inheriting from `Plugin`
2. Implement required methods: `get_name()`, `get_functions()`, `initialize()`, `cleanup()`
3. Register the plugin with `PluginManager`

Example:

```python
from app.plugins.plugin_manager import Plugin

class MyPlugin(Plugin):
    def get_name(self):
        return "myplugin"
    
    def get_functions(self):
        return {
            'my_function': self.my_function
        }
    
    def initialize(self, config):
        return True
    
    def cleanup(self):
        pass
    
    def my_function(self, arg):
        return f"Hello {arg}"
```

## Testing

Use the Swagger UI at `/docs` to test all API endpoints interactively.

## License

Copyright © 2024. All rights reserved.
