# VisuAL-1
Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# License
As all of the libraries that this tool uses are licensed under GPLv3 (or more permissive licenses), this tool is also licensed under GPLv3.

# Python Libraries required
- Numpy
- PyOpenGL
- PyQt6

# 3D Visualiser
**Current version: 0.0.3c**

Features: Have fun applying transformations to cubes and regular tetrahedra. The last position of an object before a transformation is shown as a translucent object, and the lines of vertex-wise translation and the line or plane of reflection (where applicable) is shown. The matrix stack for the active object can also be displayed. Any number of previous operations can also be repeated.

- WASD to move along the xy-plane.
- Space to move up the z-axis, Shift to move down.
- Left Click and Drag to pan the camera yaw and pitch.
- Right Click and Drag to pan the roll.
- Middle Click to reset the camera view to default position.

**Note:** Undo works on a **global** level, i.e. the operation stack is independent of the currently active object. All other features are tied to the currently active object.

# Changelog
v0.0.3b -> v0.0.3c
- Repeat feature now allows you to repeat the n most recent transformations. If n > number of transformations so far, it will automatically be rounded down to the number of transformations so far.

v0.0.3a -> v0.0.3b
- Input windows are now more user-friendly in that the interface more closely resembles what would be written on paper (particularly for vector equations of lines).
- Zero direction vector for lines or normal vector for planes is now detected and throws a native error window, and prompts the user to try again.
- Transformations equivalent to the zero transformation or identity transformation are not pushed onto the stack, even though they may appear to succeed.

v0.0.2b -> v0.0.3a
- Redid the undo API, because lmao
- Added rotation about line, projection onto plane and scaling relative to object centre
- Translation lines are now shown as translucent and vertex-wise
- Window aspect ratio of 4:3 or wider with a minimum resolution of 720 x 540, allowing full support for screen resolution of 800 x 600 or higher

# Known Bugs
- The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
