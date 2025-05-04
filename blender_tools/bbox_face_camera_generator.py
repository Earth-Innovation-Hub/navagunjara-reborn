import bpy
import mathutils
import math

def create_camera_for_face(bbox_obj, face_normal, face_center, face_size, camera_name):
    """Create an orthographic camera facing a specific bounding box face"""
    # Create a new camera
    camera_data = bpy.data.cameras.new(camera_name)
    camera_obj = bpy.data.objects.new(camera_name, camera_data)
    
    # Add to scene
    bpy.context.collection.objects.link(camera_obj)
    
    # Set to orthographic
    camera_data.type = 'ORTHO'
    
    # Calculate orthographic scale based on the face dimensions
    # We want the camera to capture the entire face
    max_dimension = max(face_size)
    camera_data.ortho_scale = max_dimension * 1.05  # Add a small margin
    
    # Position the camera
    # Move it away from the face center in the direction of the normal
    distance = max_dimension  # Distance from face
    camera_position = face_center + face_normal * distance
    camera_obj.location = camera_position
    
    # Point the camera at the face center
    direction = face_center - camera_position
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera_obj.rotation_euler = rot_quat.to_euler()
    
    return camera_obj

def get_bbox_faces(bbox_obj):
    """Get the faces of a bounding box object"""
    # Get the bounding box dimensions and center in world space
    bbox = bbox_obj.bound_box
    bbox_corners = [bbox_obj.matrix_world @ mathutils.Vector(corner) for corner in bbox]
    
    # Calculate center
    center = sum((v for v in bbox_corners), mathutils.Vector()) / 8
    
    # Calculate face normals and centers
    faces = []
    
    # Define the faces of the bounding box (indices of corners)
    face_indices = [
        [0, 1, 2, 3],  # -Z face
        [4, 5, 6, 7],  # +Z face
        [0, 1, 5, 4],  # -Y face
        [2, 3, 7, 6],  # +Y face
        [0, 3, 7, 4],  # -X face
        [1, 2, 6, 5]   # +X face
    ]
    
    face_normals = [
        mathutils.Vector((0, 0, -1)),  # -Z
        mathutils.Vector((0, 0, 1)),   # +Z
        mathutils.Vector((0, -1, 0)),  # -Y
        mathutils.Vector((0, 1, 0)),   # +Y
        mathutils.Vector((-1, 0, 0)),  # -X
        mathutils.Vector((1, 0, 0))    # +X
    ]
    
    # Transform normals to world space (only rotation, no translation)
    rot_mat = bbox_obj.matrix_world.to_3x3()
    face_normals = [rot_mat @ normal for normal in face_normals]
    
    for i, indices in enumerate(face_indices):
        # Calculate face center
        face_center = sum((bbox_corners[idx] for idx in indices), mathutils.Vector()) / 4
        
        # Calculate face dimensions
        corners = [bbox_corners[idx] for idx in indices]
        
        # Calculate width and height of the face
        width = (corners[1] - corners[0]).length
        height = (corners[3] - corners[0]).length
        
        faces.append({
            'center': face_center,
            'normal': face_normals[i],
            'size': (width, height)
        })
    
    return faces

def main():
    # Check if BoundingBoxes collection exists
    if "BoundingBoxes" not in bpy.data.collections:
        print("Collection 'BoundingBoxes' not found")
        return
    
    bbox_collection = bpy.data.collections["BoundingBoxes"]
    
    # Create a new collection for cameras if it doesn't exist
    if "BBoxCameras" not in bpy.data.collections:
        camera_collection = bpy.data.collections.new("BBoxCameras")
        bpy.context.scene.collection.children.link(camera_collection)
    else:
        camera_collection = bpy.data.collections["BBoxCameras"]
    
    # Store the original active collection
    original_collection = bpy.context.view_layer.active_layer_collection.collection
    
    # Set the camera collection as active
    for layer_collection in bpy.context.view_layer.layer_collection.children:
        if layer_collection.collection == camera_collection:
            bpy.context.view_layer.active_layer_collection = layer_collection
            break
    
    # Process each bounding box in the collection
    for i, bbox_obj in enumerate(bbox_collection.objects):
        print(f"Processing bounding box: {bbox_obj.name}")
        
        # Get the faces of the bounding box
        faces = get_bbox_faces(bbox_obj)
        
        # Create a camera for each face
        for j, face in enumerate(faces):
            camera_name = f"{bbox_obj.name}_camera_{j}"
            camera = create_camera_for_face(
                bbox_obj, 
                face['normal'], 
                face['center'], 
                face['size'], 
                camera_name
            )
            
            # Move the camera to the camera collection
            if camera.users_collection:
                for collection in camera.users_collection:
                    collection.objects.unlink(camera)
            camera_collection.objects.link(camera)
    
    # Restore the original active collection
    for layer_collection in bpy.context.view_layer.layer_collection.children:
        if layer_collection.collection == original_collection:
            bpy.context.view_layer.active_layer_collection = layer_collection
            break
    
    print("Camera generation complete")

if __name__ == "__main__":
    main() 