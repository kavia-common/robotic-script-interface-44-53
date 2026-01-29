# ROS2 Interpreter Backend

A Lua-like interpreter built on Flask with plugin support for Delta ARM APIs and ROS2 integration for robotic communication.

## Features

- **Lua-like Scripting**: Execute scripts with Lua-inspired syntax
- **Delta ARM Plugin**: Control Delta robots with comprehensive APIs
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
   - Movement control (cartesian and joint space)
   - Gripper control
   - Position querying
   - Speed and acceleration settings

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

## Script Syntax

### Variables

```lua
x = 10
name = "robot"
position = delta.get_position()
```

### Function Calls

```lua
print("Hello World")
delta.home()
delta.moveto(100, 50, -200)
```

### Delta ARM Functions

```lua
-- Home the robot
delta.home()

-- Move to position (x, y, z in mm)
delta.moveto(100, 50, -200)

-- Move joints (angles in degrees)
delta.movej(0, 45, 45)

-- Move relative
delta.move_relative(10, 0, -5)

-- Gripper control
delta.gripper_open()
delta.gripper_close()
state = delta.gripper_state()

-- Configuration
delta.set_speed(150)
delta.set_acceleration(600)

-- Query functions
pos = delta.get_position()
joints = delta.get_joints()
valid = delta.is_in_workspace(100, 50, -200)
```

## Example Scripts

### Simple Movement

```lua
-- Home the robot
delta.home()

-- Move to position
delta.moveto(100, 0, -200)
delta.moveto(0, 100, -200)
delta.moveto(-100, 0, -200)
delta.moveto(0, 0, -200)
```

### Pick and Place

```lua
-- Home robot
delta.home()

-- Open gripper
delta.gripper_open()

-- Move to pick position
delta.moveto(80, 80, -180)

-- Close gripper to grab
delta.gripper_close()

-- Move up
delta.move_relative(0, 0, 30)

-- Move to place position
delta.moveto(-80, -80, -180)

-- Open gripper to release
delta.gripper_open()

-- Move up
delta.move_relative(0, 0, 30)

-- Return home
delta.home()
```

### Speed Control

```lua
-- Home robot
delta.home()

-- Set fast speed
delta.set_speed(300)
delta.moveto(100, 0, -200)

-- Set slow speed
delta.set_speed(50)
delta.moveto(0, 100, -200)

-- Return to normal speed
delta.set_speed(100)
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
