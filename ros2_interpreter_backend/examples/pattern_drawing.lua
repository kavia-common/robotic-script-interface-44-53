-- Pattern Drawing Example
-- Draws a square pattern in 3D space

-- Home robot
delta.home()

-- Set drawing speed
delta.set_speed(100)

-- Define square corners
size = 60
height = -180

-- Move to starting position
delta.moveto(size, size, height)

-- Draw square
delta.moveto(-size, size, height)
delta.moveto(-size, -size, height)
delta.moveto(size, -size, height)
delta.moveto(size, size, height)

-- Move up
delta.move_relative(0, 0, 30)

-- Return home
delta.home()

print("Pattern drawing complete!")
