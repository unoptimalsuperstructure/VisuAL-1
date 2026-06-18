# VisuAL-1
**Current version: v0.1.2b**

Multi-purpose tool for visualising the applications of linear algebra, such as in 3D graphics rendering and data analytics.

# License
As all of the libraries that this tool uses are licensed under GPLv3 (or more permissive licenses), this tool is also licensed under GPLv3.

# Python Libraries required
- NumPy
- OpenCV-Python
- PyMongo
- PyOpenGL
- PyQt6

## What to expect for the next update
Next version: v0.1.3a - Loading and saving JSON files via the localhost MongoDB database + TLS for creating a polygon and using it to form pyramids and prisms.

# 2D Image Processing

Features: Import images as you please and move them around the canvas. Perform a simple colour filter based on your desired tint, or apply convolutions (Blur, Sharpen, Edge detection (Sobel operator)). The same operation can be applied to multiple images at a time for better efficiency.

Desktop App Controls (Moving Images):
- WASD or Left Click and Drag to move the selected images around the canvas.
- Z to move the image to the last position. (This is independent of undoing filters or convolutions.)
- H to flip the image horizontally, V to flip the image vertically.

**Note:** Undo works on a **global** level, i.e. the operation stack is independent of the currently active image(s). All other features are tied to the currently active image(s).

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
## High Priority
~~- (2D Image Processing, Desktop App) Images are not garbage collected upon closing the window, which returns to the home screen. This will be fixed by the next update.~~ (Fixed in v0.1.1b)
## Low Priority
-  (3D Visualiser, Desktop App) The camera panning code is based on the camera yaw, which does not update accurately when the camera is panned quickly. This may cause the camera to roll inadvertently and eventually mess up WASD movements. The only way to fix this is to middle-click.
- (3D Visualiser, Web App) Sometimes, object shadows will linger in their previous position even when the physical object has been reset.

# Changelog
v0.1.2a -> v0.1.2b
- Finally added shearing and custom matrices.
- Switched from a class file holding all shapes to a single abstract class file, with geometric objects being represented as JSON files instead.
- Shapes can also have their size and centre specified before adding.
- Added interface size configuration file for 3D Visualiser.

v0.1.1b -> v0.1.2a
- Ability to draw permanent lines or planes that can be shown/hidden (but not yet deleted).
- 3D objects can also now be shown/hidden, and the active object is highlighted.
- Reflection, rotation and projection can now be done with permanent lines or planes, or still allow the user to input a one-time line or plane.
- When choosing an existing line or plane for a transformation, it will be highlighted.
- After a transformation, the respective line or plane will be distinguished by being coloured yellow or blue respectively.
- Tooltips and icons showing what each operation does.

v0.1.1a -> v0.1.1b
- Fixed garbage collection.
- Ability to show or hide images.
- User is now prompted to choose a save directory, instead of being the same one as the input directory.

v0.1.0a -> v0.1.1a
- Added basic image processing features to the desktop app, including colour tint filters, median and Gaussian blur, and Sobel edge detection.
- Closing the 2D image processing or 3D graphics sandbox now returns to the home screen instead of terminating the program.

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
