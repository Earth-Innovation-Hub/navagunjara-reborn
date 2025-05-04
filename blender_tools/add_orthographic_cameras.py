import bpy
import mathutils
import math

def create_orthographic_camera(name, location, rotation, scale, ortho_scale):
    """
    Create an orthographic camera with the given parameters.
    
    Args:
        name: Name of the camera
        location: Location of the camera
        rotation: Rotation of the camera in Euler angles (radians)
        scale: Scale of the camera
        ortho_scale: Orthographic scale of the camera
    
    Returns:
        The created camera object
    """
    # Create camera data
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    
    # Create camera object
    cam_obj = bpy.data.objects.new(name, cam_data)
    
    # Link camera to scene
    bpy.context.collection.objects.link(cam_obj)
    
    # Set camera location, rotation and scale
    cam_obj.location = location
    cam_obj.rotation_euler = rotation
    cam_obj.scale = scale
    
    return cam_obj

def setup_cameras_for_bounding_box(bbox, padding=1.2):
    """
    Set up front, top, and side orthographic cameras for a bounding box.
    
    Args:
        bbox: The bounding box object
        padding: Padding factor for camera distance (default: 1.2)
    """
    # Get bounding box dimensions and center
    bbox_dimensions = bbox.dimensions
    bbox_center = bbox.location
    
    # Calculate camera distance based on the maximum dimension
    max_dim = max(bbox_dimensions)
    camera_distance = max_dim * padding
    
    # Front view camera (Y+)
    # For front view, we need to see the X and Z dimensions
    front_ortho_scale = max(bbox_dimensions.x, bbox_dimensions.z) * padding * 2
    front_loc = (bbox_center.x, bbox_center.y + camera_distance, bbox_center.z)
    front_rot = (math.pi/2, 0, math.pi)
    front_cam = create_orthographic_camera(
        f"{bbox.name}_front_cam",
        front_loc,
        front_rot,
        (1, 1, 1),
        front_ortho_scale
    )
    
    # Side view camera (X+)
    # For side view, we need to see the Y and Z dimensions
    side_ortho_scale = max(bbox_dimensions.y, bbox_dimensions.z) * padding * 2
    side_loc = (bbox_center.x + camera_distance, bbox_center.y, bbox_center.z)
    side_rot = (math.pi/2, 0, math.pi/2)
    side_cam = create_orthographic_camera(
        f"{bbox.name}_side_cam",
        side_loc,
        side_rot,
        (1, 1, 1),
        side_ortho_scale
    )
    
    # Top view camera (Z+)
    # For top view, we need to see the X and Y dimensions
    top_ortho_scale = max(bbox_dimensions.x, bbox_dimensions.y) * padding * 2
    top_loc = (bbox_center.x, bbox_center.y, bbox_center.z + camera_distance)
    top_rot = (0, 0, math.pi)
    top_cam = create_orthographic_camera(
        f"{bbox.name}_top_cam",
        top_loc,
        top_rot,
        (1, 1, 1),
        top_ortho_scale
    )
    
    # Create a collection for the cameras if it doesn't exist
    cam_collection_name = f"{bbox.name}_cameras"
    if cam_collection_name not in bpy.data.collections:
        cam_collection = bpy.data.collections.new(cam_collection_name)
        bpy.context.scene.collection.children.link(cam_collection)
    else:
        cam_collection = bpy.data.collections[cam_collection_name]
    
    # Move cameras to their collection
    for cam in [front_cam, side_cam, top_cam]:
        # Remove from current collection
        bpy.context.collection.objects.unlink(cam)
        # Add to camera collection
        cam_collection.objects.link(cam)
    
    return front_cam, side_cam, top_cam

def main():
    # Check if BoundingBoxes exists
    if "BoundingBoxes" not in bpy.data.collections:
        print("Error: BoundingBoxes collection not found")
        return
    
    bbox_collection = bpy.data.collections["BoundingBoxes"]
    
    # Create a collection for all cameras
    all_cameras_collection_name = "OrthographicCameras"
    if all_cameras_collection_name not in bpy.data.collections:
        all_cameras_collection = bpy.data.collections.new(all_cameras_collection_name)
        bpy.context.scene.collection.children.link(all_cameras_collection)
    
    # Process each bounding box in the collection
    for bbox in bbox_collection.objects:
        print(f"Setting up cameras for {bbox.name}")
        front_cam, side_cam, top_cam = setup_cameras_for_bounding_box(bbox)
        
        # Add the camera collection to the main camera collection
        cam_collection_name = f"{bbox.name}_cameras"
        if cam_collection_name in bpy.data.collections:
            # Check if already linked
            if cam_collection_name not in [c.name for c in bpy.data.collections[all_cameras_collection_name].children]:
                bpy.data.collections[all_cameras_collection_name].children.link(
                    bpy.data.collections[cam_collection_name]
                )
    
    print("Orthographic cameras setup complete!")

if __name__ == "__main__":
    main() 