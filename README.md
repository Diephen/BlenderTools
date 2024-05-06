# BlenderTools
Blender Python Tools 


## Export and Load Animation Curve
A simple tool to export/load animation curve from a selected object

- User can only select one object at a time 
- Export and load would be applying to the same object. Currently there is no check done for when the objects are not identical
- Assume there is only one layer or track for the animation. Did not account for Blender’s non-linear animation (multiple animation tracks) for now
- Export and Load opens a file browser and it is up to users’ decision on where to export or load files.
- Animation curve and key frame data reference: 

https://docs.blender.org/api/current/bpy.types.FCurve.html

https://docs.blender.org/api/current/bpy.types.Keyframe.htm



