-- Pick and Place Example
-- Demonstrates a complete pick and place operation

-- Home the robot
delta.home()

-- Configure speed for smooth operation
delta.set_speed(150)
delta.set_acceleration(500)

-- Open gripper
delta.gripper_open()

-- Move to pick position (80mm, 80mm, -180mm)
delta.moveto(80, 80, -180)

-- Close gripper to grab object
delta.gripper_close()

-- Lift object
delta.move_relative(0, 0, 30)

-- Move to place position
delta.moveto(-80, -80, -180)

-- Release object
delta.gripper_open()

-- Lift gripper
delta.move_relative(0, 0, 30)

-- Return home
delta.home()

print("Pick and place complete!")
