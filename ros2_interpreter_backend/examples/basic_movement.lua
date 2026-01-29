-- Basic Delta ARM Movement Example
-- Uses Delta API specification functions

-- First, home the robot (required before any movement)
delta.home()

-- Set global points using SetGlobalPoint
-- Six-axis format: SetGlobalPoint(point_num, name, x, y, z, rx, ry, rz, elbow, shoulder, flip, uf, tf, jrc)
delta.SetGlobalPoint(1, "GL_P1", 100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(2, "GL_P2", 0, 100, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(3, "GL_P3", -100, 0, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(4, "GL_P4", 0, -100, -200, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Move to different points using MovP (point-to-point movement)
delta.MovP(1)  -- Move to point 1
delta.MovP(2)  -- Move to point 2
delta.MovP(3)  -- Move to point 3
delta.MovP(4)  -- Move to point 4

-- Return to home position using legacy function
delta.moveto(0, 0, -200)

print("Movement complete!")
