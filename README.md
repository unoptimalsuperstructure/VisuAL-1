# VisuAL-1
Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# 3D Visualiser
Current version: 0.0.1

Features: Have fun moving a cube around the screen, and applying rotations and reflections.

Controls:
- WASD to move along the xy-plane.
- Space to move up the z-axis, Shift to move down.
- Left Click and Drag to pan the camera yaw and pitch.
- Right Click and Drag to pan the roll.
- Middle Click to reset the camera view to default position.

Known Bugs:
- The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
