# VisuAL-1
Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# License
As all of the libraries that this tool uses are licensed under GPLv3 (or more permissive licenses), this tool is also licensed under GPLv3.

# Python Libraries required
- Numpy
- PyOpenGL
- PyQt6

# 3D Visualiser
Current version: 0.0.3a

Features: Have fun applying transformations to cubes and regular tetrahedra. The last position of an object before a transformation is shown as a translucent object, and the lines of vertex-wise translation and the line or plane of reflection (where applicable) is shown. The matrix stack for the active object can also be displayed.

**Note:** Undo works on a **global** level, i.e. the operation stack is independent of the currently active object. All other features are tied to the currently active object.

Controls:
- WASD to move along the xy-plane.
- Space to move up the z-axis, Shift to move down.
- Left Click and Drag to pan the camera yaw and pitch.
- Right Click and Drag to pan the roll.
- Middle Click to reset the camera view to default position.

Known Bugs:
- The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
