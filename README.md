# VisuAL-1
Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# License
As all of the libraries that this tool uses are licensed under GPLv3 (or more permissive licenses), this tool is also licensed under GPLv3.

# Python Libraries required
- Numpy
- PyOpenGL
- PyQt6

# 3D Visualiser
Current version: 0.0.2a

Features: Have fun applying translations and reflections to unit cubes. The last position of a cube before a transformation is shown as a translucent cube, and the line of translation, or the line or plane of reflection is shown. The matrix stack for the active object can also be displayed.

Controls:
- WASD to move along the xy-plane.
- Space to move up the z-axis, Shift to move down.
- Left Click and Drag to pan the camera yaw and pitch.
- Right Click and Drag to pan the roll.
- Middle Click to reset the camera view to default position.

Known Bugs:
- The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
