# Modbus Dictionary Mode - Quick Reference

## Basic Operations

### Read Multiple Registers
```lua
device = "controller"
values = delta.ReadModbus(device, {
    ["40001"] = 1,
    ["40002"] = 1,
    ["0x1000"] = 1
})
print(values["40001"])
```

### Write Multiple Registers
```lua
delta.WriteModbus(device, {
    ["40001"] = 123,
    ["40002"] = 456,
    ["0x1000"] = 789
})
```

### Legacy Single Register (Backward Compatible)
```lua
-- Read
value = delta.ReadModbus(0x1000, "W")

-- Write
delta.WriteModbus(0x1000, "W", 100)
```

## Address Formats

| Format | Example | Description |
|--------|---------|-------------|
| Hex | `"0x1000"` | Hexadecimal address |
| Decimal | `"4096"` | Decimal address |
| Modbus | `"40001"` | Modbus holding register |

## Value Ranges

| Type | Range | Note |
|------|-------|------|
| W (16-bit) | -32,767 to 32,767 | Single word |
| DW (32-bit) | -2,147,483,648 to 2,147,483,647 | Even address required |

## Address Ranges

- **0x1000 - 0x1FFF** (4096-8191)
- **0x3000 - 0x3FFF** (12288-16383)
- **40001 - 49999** (Modbus holding registers)

## Error Handling

```lua
result = delta.WriteModbus(device, registers)
if not result.success then
    print("Errors:", result.errors)
end
```

## Common Patterns

### Status Check
```lua
status = delta.ReadModbus("plc", {
    ["40001"] = 1,  -- State
    ["40002"] = 1,  -- Error code
    ["40003"] = 1   -- Temperature
})
```

### Configuration
```lua
delta.WriteModbus("plc", {
    ["40100"] = 1,    -- Enable
    ["40101"] = 150,  -- Speed
    ["40102"] = 500   -- Acceleration
})
```

### Register Constants
```lua
REG = {
    STATE = "40001",
    ERROR = "40002",
    TEMP = "40003"
}

status = delta.ReadModbus(plc, {
    [REG.STATE] = 1,
    [REG.ERROR] = 1,
    [REG.TEMP] = 1
})
```

## Tips

✅ Use dictionary mode for multiple registers
✅ Use legacy mode for single register (optional)
✅ Define register constants for clarity
✅ Group related registers together
✅ Check result.success for error handling
✅ Even addresses for 32-bit (DW) values

## Examples

Full examples available in:
- `examples/modbus_communication.lua`
- `README.md` - Modbus section
- `MODBUS_DICTIONARY_MODE.md` - Complete guide
