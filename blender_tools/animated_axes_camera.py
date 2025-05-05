import bpy
import math
from mathutils import Vector, Quaternion

def create_camera(name, location, rotation, target_collection):
    """Create a camera at the given location with the given rotation."""
    # Create camera data
    camera_data = bpy.data.cameras.new(name)
    
    # Create camera object
    camera = bpy.data.objects.new(name, camera_data)
    camera.location = location
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = rotation
    
    # Link to the specified collection
    target_collection.objects.link(camera)
    
    return camera

def get_axes_objects():
    """Get all axes objects from the 'Axes and Fiducials' collection."""
    axes_objects = []
    
    # Find the collection
    if "Axes and Fiducials" not in bpy.data.collections:
        print("Collection 'Axes and Fiducials' not found")
        return []
    
    collection = bpy.data.collections["Axes and Fiducials"]
    
    # Get all objects in the collection that end with "_axes"
    for obj in collection.objects:
        if obj.name.endswith("_axes"):
            axes_objects.append(obj)
    
    return axes_objects

def create_camera_animation():
    """Create a camera that animates through all axes objects."""
    # Get all axes objects
    axes_objects = get_axes_objects()
    
    if not axes_objects:
        print("No axes objects found")
        return
    
    print(f"Found {len(axes_objects)} axes objects")
    
    # Create a new collection for the camera
    camera_collection = bpy.data.collections.new("Camera Animation")
    bpy.context.scene.collection.children.link(camera_collection)
    
    # Get the first axes object to position the camera
    first_axes = axes_objects[0]
    
    # Create the camera with an offset from the axes
    offset_distance = 5.0  # Distance from the axes
    offset_direction = Vector((0, -1, 0.5)).normalized()  # Direction of the offset
    
    # Create initial camera location with offset
    camera_location = first_axes.location + offset_direction * offset_distance
    
    # Create a camera that looks at the first axes
    camera = create_camera("Animated_Camera", camera_location, first_axes.rotation_quaternion, camera_collection)
    
    # Set the camera as the active camera
    bpy.context.scene.camera = camera
    
    # Calculate total animation duration
    frame_per_axis = 30  # Number of frames to stay at each axis
    transition_frames = 40  # Number of frames for transition between axes
    total_frames = len(axes_objects) * (frame_per_axis + transition_frames)
    
    # Set scene frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = total_frames
    
    # Create animation
    current_frame = 1
    
    for i, axes in enumerate(axes_objects):
        # Calculate the camera position with offset from the current axes
        camera_location = axes.location + offset_direction * offset_distance
        
        # Look-at constraint would be ideal, but for simplicity we'll just use the axes rotation
        # with a slight adjustment to point the camera at the axes
        camera_rotation = axes.rotation_quaternion.copy()
        
        # Insert keyframe for location and rotation
        camera.location = camera_location
        camera.keyframe_insert(data_path="location", frame=current_frame)
        
        camera.rotation_quaternion = camera_rotation
        camera.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
        
        # Move to the frame where we start transitioning to the next axes
        current_frame += frame_per_axis
        
        # Insert the same keyframe at this frame to create a hold
        camera.keyframe_insert(data_path="location", frame=current_frame)
        camera.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
        
        # Move to the frame where we should be at the next axes
        current_frame += transition_frames
        
        # If this is the last axes, create keyframes to loop back to the first axes
        if i == len(axes_objects) - 1:
            first_axes = axes_objects[0]
            camera_location = first_axes.location + offset_direction * offset_distance
            camera_rotation = first_axes.rotation_quaternion.copy()
            
            camera.location = camera_location
            camera.keyframe_insert(data_path="location", frame=current_frame)
            
            camera.rotation_quaternion = camera_rotation
            camera.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
    
    # Set interpolation for smoother animation
    for fcurve in camera.animation_data.action.fcurves:
        for keyframe_point in fcurve.keyframe_points:
            keyframe_point.interpolation = 'BEZIER'
    
    # Create a track-to constraint so the camera always points at the axes
    track_constraint = camera.constraints.new('TRACK_TO')
    empty = bpy.data.objects.new("Camera_Target", None)
    empty.hide_viewport = True
    camera_collection.objects.link(empty)
    
    # Create an animation for the empty to follow the axes
    current_frame = 1
    for i, axes in enumerate(axes_objects):
        empty.location = axes.location
        empty.keyframe_insert(data_path="location", frame=current_frame)
        
        # Hold at current axes
        current_frame += frame_per_axis
        empty.keyframe_insert(data_path="location", frame=current_frame)
        
        # Move to the next axes
        current_frame += transition_frames
        
        # If this is the last axes, loop back to the first
        if i == len(axes_objects) - 1:
            empty.location = axes_objects[0].location
            empty.keyframe_insert(data_path="location", frame=current_frame)
    
    # Set up the track-to constraint
    track_constraint.target = empty
    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_constraint.up_axis = 'UP_Y'
    
    # Set animation to repeat
    if camera.animation_data and camera.animation_data.action:
        camera.animation_data.action.use_cyclic = True
    if empty.animation_data and empty.animation_data.action:
        empty.animation_data.action.use_cyclic = True
    
    print("Camera animation created successfully!")
    return camera

if __name__ == "__main__":
    create_camera_animation() 