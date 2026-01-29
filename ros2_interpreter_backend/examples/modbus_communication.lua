-- Modbus Communication Example
-- Demonstrates dictionary-based Modbus register read/write operations

-- Home the robot first
delta.home()

print("=== Modbus Dictionary-Based Communication Example ===")

-- Dictionary Mode (NEW - Recommended)
-- Write multiple registers using dictionary
print("\n1. Writing to Modbus registers using dictionary mode...")
device = "robot_controller"

-- Write values to multiple registers at once
write_result = delta.WriteModbus(device, {
    ["40001"] = 123,
    ["40002"] = 456,
    ["40010"] = 789,
    ["0x1000"] = 100,
    ["0x1002"] = 500
})

print("Write result:", write_result)

-- Read multiple registers using dictionary
print("\n2. Reading from Modbus registers using dictionary mode...")
read_result = delta.ReadModbus(device, {
    ["40001"] = 1,  -- Read 1 register at address 40001
    ["40002"] = 1,  -- Read 1 register at address 40002
    ["40010"] = 1,  -- Read 1 register at address 40010
    ["0x1000"] = 1, -- Read 1 register at hex address 0x1000
    ["0x1002"] = 1  -- Read 1 register at hex address 0x1002
})

print("Read result:", read_result)
print("Value at 40001:", read_result["40001"])
print("Value at 40002:", read_result["40002"])
print("Value at 0x1000:", read_result["0x1000"])

-- Practical example: Using Modbus for sensor data
print("\n3. Practical example: Reading sensor data...")

-- Write sensor configuration
delta.WriteModbus(device, {
    ["40100"] = 1,    -- Enable sensor 1
    ["40101"] = 1,    -- Enable sensor 2
    ["40102"] = 50    -- Set threshold to 50
})

-- Simulate sensor data write
delta.WriteModbus(device, {
    ["40200"] = 75,   -- Sensor 1 reading
    ["40201"] = 82,   -- Sensor 2 reading
    ["40202"] = 1     -- Status: OK
})

-- Read sensor data
sensor_data = delta.ReadModbus(device, {
    ["40200"] = 1,
    ["40201"] = 1,
    ["40202"] = 1
})

print("Sensor 1 reading:", sensor_data["40200"])
print("Sensor 2 reading:", sensor_data["40201"])
print("Status:", sensor_data["40202"])

-- Legacy Mode (Backward Compatibility)
print("\n4. Legacy mode - individual register operations...")

-- Write single register (legacy syntax)
delta.WriteModbus(0x1010, "W", 999)
print("Wrote 999 to register 0x1010 using legacy mode")

-- Read single register (legacy syntax)
value = delta.ReadModbus(0x1010, "W")
print("Read value from 0x1010:", value)

-- Write 32-bit value (DW - must use even address)
delta.WriteModbus(0x1020, "DW", 100000)
print("Wrote 100000 to register 0x1020 (32-bit)")

-- Read 32-bit value
dw_value = delta.ReadModbus(0x1020, "DW")
print("Read 32-bit value from 0x1020:", dw_value)

-- Example: Coordinated movement with Modbus control
print("\n5. Coordinated movement with Modbus status...")

-- Set up points for movement
delta.SetGlobalPoint(50, "GL_Station1", 80, 80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(51, "GL_Station2", -80, -80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Write status: Moving to station 1
delta.WriteModbus(device, {["40300"] = 1})  -- Status: Moving
delta.MovL(50)
delta.WriteModbus(device, {["40300"] = 2})  -- Status: At station 1

delta.DELAY(0.5)

-- Write status: Moving to station 2
delta.WriteModbus(device, {["40300"] = 1})  -- Status: Moving
delta.MovL(51)
delta.WriteModbus(device, {["40300"] = 2})  -- Status: At station 2

-- Return home and write completion status
delta.home()
delta.WriteModbus(device, {["40300"] = 0})  -- Status: Idle

print("\n=== Modbus communication example complete! ===")
