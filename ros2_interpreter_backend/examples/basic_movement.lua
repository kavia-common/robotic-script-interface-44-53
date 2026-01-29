-- Basic Delta ARM Movement Example
-- This script demonstrates basic movement commands

-- First, home the robot (required before any movement)
delta.home()

-- Move to different positions
-- Coordinates are in millimeters (x, y, z)
delta.moveto(100, 0, -200)
delta.moveto(0, 100, -200)
delta.moveto(-100, 0, -200)
delta.moveto(0, -100, -200)

-- Return to center
delta.moveto(0, 0, -200)

print("Movement complete!")
