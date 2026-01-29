-- Pick and Place Example
-- Uses Delta API specification functions

-- Home the robot
delta.home()

-- Configure speed using Delta API (percentage for joint movements)
delta.SpdJ(50)  -- Set joint speed to 50%
delta.AccJ(50)  -- Set joint acceleration to 50%

-- Configure linear speed for linear movements
delta.SpdL(150)  -- Set linear speed to 150 mm/sec
delta.AccL(500)  -- Set linear acceleration to 500 mm/sec²

-- Set global points for pick and place locations
delta.SetGlobalPoint(10, "GL_Pick", 80, 80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(11, "GL_PickUp", 80, 80, -150, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(12, "GL_Place", -80, -80, -180, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(13, "GL_PlaceUp", -80, -80, -150, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Open gripper (using DO for gripper control)
delta.DO(1, "OFF")

-- Move to pick position using linear movement
delta.MovL(10)

-- Close gripper to grab object
delta.DO(1, "ON")
delta.DELAY(0.5)  -- Wait for gripper to close

-- Lift object
delta.MovL(11)

-- Move to place position
delta.MovL(12)

-- Release object
delta.DO(1, "OFF")
delta.DELAY(0.5)

-- Lift gripper
delta.MovL(13)

-- Return home
delta.home()

print("Pick and place complete!")
