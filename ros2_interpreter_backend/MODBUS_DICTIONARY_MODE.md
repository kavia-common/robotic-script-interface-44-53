# Modbus Dictionary Mode Implementation

## Overview

The Delta ARM plugin now supports **dictionary-based Modbus register access**, providing a more intuitive and efficient way to read and write multiple Modbus registers.

## Key Features

### 1. Dictionary-Based API

- **Read multiple registers**: Single call to read multiple registers
- **Write multiple registers**: Batch write operations
- **Flexible addressing**: Support for decimal, hexadecimal, and Modbus-style addresses
- **Automatic validation**: Address and value range validation
- **Clear error messages**: Detailed error reporting for invalid operations

### 2. Backward Compatibility

Legacy single-register mode is fully supported for existing code.

## API Reference

### ReadModbus (Dictionary Mode)

```python
ReadModbus(device, register_map) -> Dict[str, int]
```

**Parameters:**
- `device`: Device identifier (any type - string, int, etc.)
- `register_map`: Dictionary mapping register addresses (string) to read counts (int)

**Returns:**
- Dictionary mapping register addresses (string) to values (int)
- `None` on error

**Example:**
```lua
device = "plc_controller"
values = delta.ReadModbus(device, {
    ["40001"] = 1,      -- Read 1 register at 40001
    ["40002"] = 1,      -- Read 1 register at 40002
    ["0x1000"] = 1      -- Read 1 register at hex 0x1000
})

-- Access values
print(values["40001"])
print(values["0x1000"])
```

### WriteModbus (Dictionary Mode)

```python
WriteModbus(device, register_map) -> Dict[str, Any]
```

**Parameters:**
- `device`: Device identifier
- `register_map`: Dictionary mapping register addresses (string) to values (int)

**Returns:**
- Status dictionary with keys:
  - `success`: Boolean indicating overall success
  - `message`: Human-readable status message
  - `written`: Number of registers successfully written
  - `errors`: List of error messages (if any)

**Example:**
```lua
result = delta.WriteModbus(device, {
    ["40001"] = 123,
    ["40002"] = 456,
    ["0x1000"] = 789
})

print("Success:", result.success)
print("Written:", result.written)
```

### ReadModbus (Legacy Mode)

```python
ReadModbus(address, size) -> int
```

**Parameters:**
- `address`: Register address (integer, hex format like 0x1000)
- `size`: "W" for 16-bit or "DW" for 32-bit

**Returns:**
- Register value (int)
- `None` on error

**Example:**
```lua
value = delta.ReadModbus(0x1000, "W")
dw_value = delta.ReadModbus(0x1002, "DW")
```

### WriteModbus (Legacy Mode)

```python
WriteModbus(address, size, value) -> Dict[str, Any]
```

**Parameters:**
- `address`: Register address (integer)
- `size`: "W" for 16-bit or "DW" for 32-bit
- `value`: Value to write (integer)

**Returns:**
- Status dictionary

**Example:**
```lua
delta.WriteModbus(0x1000, "W", 100)
delta.WriteModbus(0x1002, "DW", 50000)
```

## Supported Address Formats

### Hexadecimal Addresses
- Format: `"0x1000"`, `"0x1002"`, `"0x3000"`, etc.
- Range: 0x1000-0x1FFF, 0x3000-0x3FFF

### Decimal Addresses
- Format: `"4096"`, `"4098"`, `"12288"`, etc.
- Same numeric values as hex addresses

### Modbus Holding Register Addresses
- Format: `"40001"`, `"40002"`, `"40003"`, etc.
- Range: 40001-49999

## Value Ranges

### 16-bit Word (W)
- Range: -32,767 to 32,767
- Automatically inferred for values in this range

### 32-bit Double Word (DW)
- Range: -2,147,483,648 to 2,147,483,647
- **Requires even address** (0x1000, 0x1002, but NOT 0x1001)

## Error Handling

### Invalid Address
```lua
-- Invalid address format
result = delta.WriteModbus(device, {
    ["invalid"] = 123
})
-- Returns: success=false, errors=["Invalid register address: invalid"]
```

### Out of Range Address
```lua
-- Address outside supported ranges
result = delta.WriteModbus(device, {
    ["99999"] = 123
})
-- Returns: success=false, errors=["Register address 99999 out of supported range"]
```

### Value Out of Range
```lua
-- Value too large for any register type
result = delta.WriteModbus(device, {
    ["40001"] = 3000000000
})
-- Returns: success=false, errors=["Register 40001: value ... out of range"]
```

### DW on Odd Address
```lua
-- 32-bit value on odd address
result = delta.WriteModbus(device, {
    ["0x1001"] = 100000
})
-- Returns: success=false, errors=["Register 0x1001: DW values require even address"]
```

## Use Cases

### 1. Batch Status Reading

```lua
device = "robot_status"

-- Read multiple status registers at once
status = delta.ReadModbus(device, {
    ["40001"] = 1,  -- Robot state
    ["40002"] = 1,  -- Current position
    ["40003"] = 1,  -- Speed
    ["40004"] = 1,  -- Error code
    ["40005"] = 1   -- Temperature
})

print("State:", status["40001"])
print("Position:", status["40002"])
print("Speed:", status["40003"])
print("Error:", status["40004"])
print("Temperature:", status["40005"])
```

### 2. Configuration Setup

```lua
device = "plc"

-- Write configuration to PLC
delta.WriteModbus(device, {
    ["40100"] = 1,      -- Enable flag
    ["40101"] = 150,    -- Speed setpoint
    ["40102"] = 500,    -- Acceleration
    ["40103"] = 75,     -- Temperature limit
    ["40104"] = 2       -- Operating mode
})
```

### 3. Sensor Array Reading

```lua
device = "sensor_array"

-- Read all sensors at once
sensors = delta.ReadModbus(device, {
    ["40200"] = 1,  -- Sensor 1
    ["40201"] = 1,  -- Sensor 2
    ["40202"] = 1,  -- Sensor 3
    ["40203"] = 1,  -- Sensor 4
    ["40204"] = 1,  -- Sensor 5
    ["40205"] = 1   -- Sensor 6
})

-- Process sensor data
for i = 1, 6 do
    addr = string.format("402%02d", i - 1 + 200)
    print("Sensor " .. i .. ":", sensors[addr])
end
```

### 4. Coordinated I/O and Movement

```lua
device = "control_system"

-- Initialize
delta.home()

-- Write start status
delta.WriteModbus(device, {
    ["40001"] = 1,  -- Status: Starting
    ["40002"] = 0   -- Progress: 0%
})

-- Set up positions
delta.SetGlobalPoint(1, "GL_P1", 100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Move and update progress
delta.WriteModbus(device, {["40001"] = 2, ["40002"] = 50})  -- Moving, 50%
delta.MovP(1)

-- Complete
delta.WriteModbus(device, {["40001"] = 3, ["40002"] = 100}) -- Complete, 100%
```

### 5. Mixed Address Format Usage

```lua
device = "mixed_controller"

-- Mix decimal, hex, and Modbus addresses
data = delta.ReadModbus(device, {
    ["40001"] = 1,      -- Modbus format
    ["0x1000"] = 1,     -- Hex format
    ["4098"] = 1        -- Decimal format
})

-- All formats work together
print("Modbus addr 40001:", data["40001"])
print("Hex addr 0x1000:", data["0x1000"])
print("Decimal addr 4098:", data["4098"])
```

## Migration Guide

### From Array Indexing (if applicable)

If you were using array-style indexing (which is now replaced):

**Old approach (hypothetical array mode):**
```lua
-- This is NOT how it worked before, but illustrates the concept
registers = {100, 200, 300}
delta.WriteModbusArray(0x1000, registers)
```

**New dictionary mode:**
```lua
device = "controller"
delta.WriteModbus(device, {
    ["0x1000"] = 100,
    ["0x1001"] = 200,
    ["0x1002"] = 300
})
```

### From Individual Calls

**Before:**
```lua
delta.WriteModbus(0x1000, "W", 100)
delta.WriteModbus(0x1001, "W", 200)
delta.WriteModbus(0x1002, "W", 300)
delta.WriteModbus(0x1003, "W", 400)
delta.WriteModbus(0x1004, "W", 500)
```

**After:**
```lua
device = "controller"
delta.WriteModbus(device, {
    ["0x1000"] = 100,
    ["0x1001"] = 200,
    ["0x1002"] = 300,
    ["0x1003"] = 400,
    ["0x1004"] = 500
})
```

## Best Practices

1. **Use meaningful device identifiers**
   ```lua
   robot_plc = "main_plc"
   sensor_controller = "sensor_hub"
   ```

2. **Group related registers**
   ```lua
   -- Good: Related registers together
   status = delta.ReadModbus(plc, {
       ["40001"] = 1,  -- state
       ["40002"] = 1,  -- mode
       ["40003"] = 1   -- error
   })
   ```

3. **Define register constants**
   ```lua
   REG = {
       STATUS = "40001",
       MODE = "40002",
       SPEED = "40003"
   }
   
   status = delta.ReadModbus(plc, {
       [REG.STATUS] = 1,
       [REG.MODE] = 1,
       [REG.SPEED] = 1
   })
   ```

4. **Handle errors explicitly**
   ```lua
   result = delta.WriteModbus(device, registers)
   if not result.success then
       print("Write failed:", result.message)
       for _, error in ipairs(result.errors) do
           print("  Error:", error)
       end
   end
   ```

5. **Use dictionary mode for batch operations**
   - Reduces overhead
   - Clearer code intent
   - Better error handling

## Performance Considerations

- Dictionary mode is more efficient for multiple registers
- Single operation vs. multiple calls
- Reduced parsing overhead
- Better for real-time applications

## Compatibility Notes

- **Backward Compatible**: Legacy single-register mode still works
- **No Breaking Changes**: Existing scripts continue to work
- **Recommended**: Use dictionary mode for new development
- **Future-Proof**: Dictionary mode is the recommended standard going forward

## Testing

See `examples/modbus_communication.lua` for comprehensive examples demonstrating:
- Dictionary mode read/write
- Legacy mode compatibility
- Error handling
- Mixed address formats
- Practical use cases

## Summary

Dictionary-based Modbus access provides:
✅ Clearer, more maintainable code
✅ Batch operations for efficiency
✅ Better error handling and validation
✅ Full backward compatibility
✅ Flexible address format support
✅ Aligned with Delta API specification

For questions or issues, refer to the README.md or example scripts.
