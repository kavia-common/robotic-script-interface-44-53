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

The Modbus functions now support **dictionary-based register access** for improved usability and flexibility.

#### Dictionary Mode (Recommended)

```lua
-- Read multiple Modbus registers using dictionary
device = "robot_controller"
values = delta.ReadModbus(device, {
    ["40001"] = 1,    -- Read 1 register at address 40001
    ["40002"] = 1,    -- Read 1 register at address 40002
    ["0x1000"] = 1    -- Read 1 register at hex address 0x1000
})

-- Access read values
print(values["40001"])  -- Prints the value at register 40001
print(values["0x1000"]) -- Prints the value at register 0x1000

-- Write multiple Modbus registers using dictionary
delta.WriteModbus(device, {
    ["40001"] = 123,     -- Write 123 to register 40001
    ["40002"] = 456,     -- Write 456 to register 40002
    ["0x1000"] = 100     -- Write 100 to hex address 0x1000
})
```

**Supported Address Formats:**
- Decimal: `"40001"`, `"40002"`, etc. (Modbus holding registers)
- Hexadecimal: `"0x1000"`, `"0x1002"`, etc.
- Numeric ranges:
  - 0x1000-0x1FFF (4096-8191)
  - 0x3000-0x3FFF (12288-16383)
  - 40001-49999 (Modbus holding register addresses)

**Value Ranges:**
- 16-bit (W): -32,767 to 32,767
- 32-bit (DW): -2,147,483,648 to 2,147,483,647 (requires even address)

#### Legacy Mode (Backward Compatibility)

```lua
-- Read single Modbus register (legacy syntax)
value = delta.ReadModbus(0x1000, "W")   -- Read 16-bit register
value = delta.ReadModbus(0x1000, "DW")  -- Read 32-bit register

-- Write single Modbus register (legacy syntax)
delta.WriteModbus(0x1000, "W", 100)     -- Write 16-bit value
delta.WriteModbus(0x1002, "DW", 50000)  -- Write 32-bit value (even address required)
```

**Note:** Legacy mode is maintained for backward compatibility. New code should use dictionary mode for better clarity and batch operations.

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

### Modbus Communication with Movement Coordination

```lua
-- Home robot
delta.home()

-- Device identifier
device = "plc_controller"

-- Set up work stations
delta.SetGlobalPoint(10, "GL_Station1", 80, 80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(11, "GL_Station2", -80, -80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Configure Modbus registers for status reporting
status_registers = {
    ["40001"] = 0,    -- Robot status (0=idle, 1=moving, 2=at_station)
    ["40002"] = 0,    -- Current station (0=home, 1=station1, 2=station2)
    ["40003"] = 0     -- Operation count
}

-- Initialize status
delta.WriteModbus(device, status_registers)

-- Read configuration from PLC
config = delta.ReadModbus(device, {
    ["40100"] = 1,    -- Speed setting
    ["40101"] = 1,    -- Number of cycles
    ["40102"] = 1     -- Enable flag
})

if config["40102"] == 1 then
    -- Set speed based on PLC configuration
    delta.SpdL(config["40100"])
    
    -- Execute movement cycle
    delta.WriteModbus(device, {["40001"] = 1, ["40002"] = 1})  -- Moving to station 1
    delta.MovL(10)
    delta.WriteModbus(device, {["40001"] = 2})  -- At station 1
    delta.DELAY(0.5)
    
    delta.WriteModbus(device, {["40001"] = 1, ["40002"] = 2})  -- Moving to station 2
    delta.MovL(11)
    delta.WriteModbus(device, {["40001"] = 2})  -- At station 2
    delta.DELAY(0.5)
    
    -- Return home
    delta.home()
    delta.WriteModbus(device, {["40001"] = 0, ["40002"] = 0, ["40003"] = 1})  -- Idle, increment count
end

print("Coordinated operation complete!")
```

### Sensor Monitoring with Modbus

```lua
-- Home robot
delta.home()

device = "sensor_module"

-- Configure sensors via Modbus
delta.WriteModbus(device, {
    ["40001"] = 1,     -- Enable temperature sensor
    ["40002"] = 1,     -- Enable pressure sensor
    ["40003"] = 75,    -- Temperature threshold
    ["40004"] = 100    -- Pressure threshold
})

-- Set up inspection point
delta.SetGlobalPoint(20, "GL_Inspect", 0, 0, -150, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Move to inspection position
delta.MovL(20)

-- Read sensor values
sensor_data = delta.ReadModbus(device, {
    ["40100"] = 1,     -- Temperature reading
    ["40101"] = 1,     -- Pressure reading
    ["40102"] = 1      -- Sensor status
})

temperature = sensor_data["40100"]
pressure = sensor_data["40101"]
status = sensor_data["40102"]

print("Temperature:", temperature)
print("Pressure:", pressure)
print("Status:", status)

-- Check thresholds and take action
if temperature > 75 then
    print("Temperature warning!")
    delta.WriteModbus(device, {["40200"] = 1})  -- Set alarm flag
end

if pressure > 100 then
    print("Pressure warning!")
    delta.WriteModbus(device, {["40201"] = 1})  -- Set alarm flag
end

-- Return home
delta.home()
delta.WriteModbus(device, {["40200"] = 0, ["40201"] = 0})  -- Clear alarms
```

## Modbus Dictionary Mode Migration Guide

### Why Dictionary Mode?

Dictionary-based Modbus access provides several advantages:

1. **Clarity**: Register addresses are explicit in the code
2. **Batch Operations**: Read/write multiple registers in one call
3. **Flexibility**: Mix different address formats (decimal, hex)
4. **Type Safety**: Automatic value range validation
5. **Better Error Messages**: Invalid addresses are clearly identified

### Migrating from Legacy Mode

**Before (Legacy Array/Single-Register Mode):**
```lua
-- Reading individual registers
value1 = delta.ReadModbus(0x1000, "W")
value2 = delta.ReadModbus(0x1002, "W")
value3 = delta.ReadModbus(0x1004, "W")

-- Writing individual registers
delta.WriteModbus(0x1000, "W", 100)
delta.WriteModbus(0x1002, "W", 200)
delta.WriteModbus(0x1004, "W", 300)
```

**After (Dictionary Mode):**
```lua
-- Reading multiple registers at once
device = "controller"
values = delta.ReadModbus(device, {
    ["0x1000"] = 1,
    ["0x1002"] = 1,
    ["0x1004"] = 1
})

-- Writing multiple registers at once
delta.WriteModbus(device, {
    ["0x1000"] = 100,
    ["0x1002"] = 200,
    ["0x1004"] = 300
})
```

### Address Format Conversion

| Legacy (Hex)  | Dictionary Format | Alternative Format |
|---------------|-------------------|--------------------|
| `0x1000`      | `"0x1000"`        | `"4096"`           |
| `0x1002`      | `"0x1002"`        | `"4098"`           |
| `0x3000`      | `"0x3000"`        | `"12288"`          |
| N/A           | `"40001"`         | Modbus holding reg |
| N/A           | `"40002"`         | Modbus holding reg |

### Best Practices

1. **Use Dictionary Mode for New Code**: It's more maintainable and efficient
2. **Group Related Registers**: Read/write related registers together
3. **Use Meaningful Address Names**: Consider using variables for common addresses
4. **Handle Errors**: Check return values from WriteModbus for error messages
5. **Document Register Maps**: Keep a clear mapping of register addresses and their purposes

Example with register map:
```lua
-- Define register map as constants
REGISTERS = {
    STATUS = "40001",
    POSITION = "40002",
    SPEED = "40003",
    TEMPERATURE = "40100",
    PRESSURE = "40101"
}

-- Use named registers for clarity
status_data = delta.ReadModbus(device, {
    [REGISTERS.STATUS] = 1,
    [REGISTERS.POSITION] = 1,
    [REGISTERS.SPEED] = 1
})

print("Robot status:", status_data[REGISTERS.STATUS])
print("Current position:", status_data[REGISTERS.POSITION])
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
