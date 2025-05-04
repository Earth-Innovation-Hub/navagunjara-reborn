import bpy
import math

def create_animated_camera():
    # Check if BBoxCameras collection exists
    if "BBoxCameras" not in bpy.data.collections:
        print("Error: BBoxCameras collection not found")
        return
    
    # Get all cameras from the BBoxCameras collection
    bbox_cameras = []
    for obj in bpy.data.collections["BBoxCameras"].objects:
        if obj.type == 'CAMERA':
            bbox_cameras.append(obj)
    
    if not bbox_cameras:
        print("Error: No cameras found in BBoxCameras collection")
        return
    
    print(f"Found {len(bbox_cameras)} cameras in BBoxCameras collection")
    
    # Create a new camera for animation
    animated_cam_data = bpy.data.cameras.new(name="AnimatedCamera")
    animated_cam = bpy.data.objects.new("AnimatedCamera", animated_cam_data)
    
    # Add to scene
    if "CameraAnimation" not in bpy.data.collections:
        cam_anim_collection = bpy.data.collections.new("CameraAnimation")
        bpy.context.scene.collection.children.link(cam_anim_collection)
    else:
        cam_anim_collection = bpy.data.collections["CameraAnimation"]
    
    cam_anim_collection.objects.link(animated_cam)
    
    # Set up animation
    scene = bpy.context.scene
    fps = scene.render.fps
    
    # Calculate total animation length
    frames_per_camera = 30  # Stay on each camera for 1 second (assuming 30fps)
    total_frames = len(bbox_cameras) * frames_per_camera
    
    # Set scene end frame
    scene.frame_end = total_frames
    
    # Create keyframes for each camera position
    for i, camera in enumerate(bbox_cameras):
        frame = i * frames_per_camera
        
        # Go to frame
        scene.frame_set(frame)
        
        # Set animated camera to match the current bbox camera
        animated_cam.location = camera.location.copy()
        animated_cam.rotation_euler = camera.rotation_euler.copy()
        
        # Set keyframes for location and rotation
        animated_cam.keyframe_insert(data_path="location", frame=frame)
        animated_cam.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    # Make the scene use our animated camera
    scene.camera = animated_cam
    
    # Set interpolation method to make transitions smoother
    for fcurve in animated_cam.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'BEZIER'
    
    print(f"Created animated camera with {len(bbox_cameras)} positions")
    return animated_cam

if __name__ == "__main__":
    create_animated_camera() 