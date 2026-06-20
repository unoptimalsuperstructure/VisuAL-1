Pass in an nx2 or nx3 array as a CSV.
If a nx3 array is entered, the best fit polygon will be derived using TLS.
If the points cannot be fitted to a plane, the program will say so.
Note that the program does NOT protect against duplicate points.
The purpose of this feature is to allow users to input custom polygons that are close to true polygons, but are off due to rounding errors. Hence, we do not guarantee that the internal algorithm is 100% fail-safe.
Also, non-simple (self-intersecting) polygons are NOT RECOMMENDED as they are known to cause rendering issues.