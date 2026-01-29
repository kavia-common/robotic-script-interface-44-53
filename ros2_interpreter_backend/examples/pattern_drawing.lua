-- Pattern Drawing Example
-- Draws a square pattern using Delta API

-- Home robot
delta.home()

-- Set drawing speed using linear speed control
delta.SpdL(100)  -- 100 mm/sec
delta.AccL(500)  -- 500 mm/sec²

-- Set accuracy for smooth movement
delta.Accur("HIGH", "CART")

-- Define square corners as global points
size = 60
height = -180

delta.SetGlobalPoint(20, "GL_Corner1", size, size, height, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(21, "GL_Corner2", -size, size, height, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(22, "GL_Corner3", -size, -size, height, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})
delta.SetGlobalPoint(23, "GL_Corner4", size, -size, height, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,0,0,0,0,0})

-- Move to starting position
delta.MovL(20)

-- Draw square using linear movements
delta.MovL(21)
delta.MovL(22)
delta.MovL(23)
delta.MovL(20)  -- Complete the square

-- Move up using relative movement
delta.move_relative(0, 0, 30)

-- Return home
delta.home()

print("Pattern drawing complete!")
