# VisuAL-1
**Current version: v0.1.0**

Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# License
As all of the libraries that this tool uses are licensed under GPLv3 (or more permissive licenses), this tool is also licensed under GPLv3.

# Python Libraries required
- Numpy
- OpenCV-Python (only from v0.1.1a onwards)
- PyOpenGL
- PyQt6

## What to expect for the next update
Next version: v0.1.1a - will include basic image processing features.

# 3D Visualiser

Features: Have fun applying transformations to cubes and regular tetrahedra. The last position of an object before a transformation is shown as a translucent object, and the lines of vertex-wise translation and the line or plane of reflection (where applicable) is shown. The matrix stack for the active object can also be displayed. Any number of previous operations can also be repeated.

Desktop App Controls (Game Camera):
- WASD to move along the xy-plane.
- Space to move up the z-axis, Shift to move down.
- Left Click and Drag to pan the camera yaw and pitch.
- Right Click and Drag to pan the roll.
- Middle Click to reset the camera view to default position.

Web App Controls (Spherical Coordinates):
- W and S to change the radius.
- A and D to change the azimuthal angle.
- Space and Shift to change the polar angle.
- (Alternatively) Left Click and Drag to change the azimuthal and polar angles.
- Middle Click to reset the camera view to default position.

**Note:** Undo works on a **global** level, i.e. the operation stack is independent of the currently active object. All other features are tied to the currently active object.

# Known Bugs
- (Desktop App) The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
- (Web App) Sometimes, object shadows will linger in their previous position even when the physical object has been reset.

# Changelog
v0.0.3c -> v0.1.0a
- Merged Desktop App v0.0.3c and Web App to the main branch.

v0.0.3b -> v0.0.3c
- Repeat feature now allows you to repeat the n most recent transformations. If n > number of transformations so far, it will automatically be rounded down to the number of transformations so far.

v0.0.3a -> v0.0.3b
- Input windows are now more user-friendly in that the interface more closely resembles what would be written on paper (particularly for vector equations of lines).
- Zero direction vector for lines or normal vector for planes is now detected and throws a native error window, and prompts the user to try again.
- Transformations equivalent to the zero transformation or identity transformation are not pushed onto the stack, even though they may appear to succeed.

v0.0.2b -> v0.0.3a
- Added regular tetrahedra.
- Redid the undo API, because lmao
- Added the repeat feature to repeat the last transformation, if any.
- Added rotation about line, projection onto plane and scaling relative to object centre
- Translation lines are now shown as translucent and vertex-wise
- Window aspect ratio of 4:3 or wider with a minimum resolution of 720 x 540, allowing full support for screen resolution of 800 x 600 or higher

v0.0.2a -> v0.0.2b
- Added the matrix stack feature.

v0.01 -> v0.0.2a
- The last position of a cube before a transformation is shown as a translucent cube, and the line of translation, or the line or plane of reflection is shown.

v0.0.1
- A unit cube is drawn on the screen by default. One can apply translations and reflections to it.
