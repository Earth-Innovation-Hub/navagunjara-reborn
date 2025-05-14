import FreeCAD as App
import Part
import ObjectsFem
import Fem
from FreeCAD import Base
import math
import random

# Open a new document
doc = App.newDocument("ArtisticTrussStructure")

# =========== Create an artistic truss structure ===========
# Define dimensions
base_width = 4.0    # Width of the base
base_depth = 4.0    # Depth of the base
height = 8.0        # Total height
beam_radius = 0.08  # Thickness of beams

# Create a compound shape to hold all structure elements
lines = []

# Function to create a bezier curve
def make_bezier_curve(points, num_segments=20):
    bezier = Part.BezierCurve()
    bezier.setPoles(points)
    return bezier.toShape()

# Create base platform (hexagonal)
base_points = []
for i in range(6):
    angle = i * math.pi / 3
    x = base_width/2 * math.cos(angle)
    y = base_width/2 * math.sin(angle)
    base_points.append(Base.Vector(x, y, 0))

# Close the hexagon
base_points.append(base_points[0])

# Create the base perimeter
for i in range(len(base_points)-1):
    lines.append(Part.makePolygon([base_points[i], base_points[i+1]]))

# Create cross supports for the base
for i in range(0, 6, 2):
    j = (i + 3) % 6  # Connect to opposite point
    lines.append(Part.makePolygon([base_points[i], base_points[j]]))

# Create vertical supports (3 columns)
column_tops = []
column_bases = [
    base_points[0],  # First column at first corner
    base_points[2],  # Second column at third corner
    base_points[4]   # Third column at fifth corner
]

# Create curved columns with varying height
for i, base in enumerate(column_bases):
    # Each column has a different height
    col_height = height * (0.75 + i * 0.12)
    
    # Create control points for the bezier curve
    control_points = [
        base,
        Base.Vector(base.x * 1.2, base.y * 1.2, col_height * 0.3),
        Base.Vector(base.x * 0.8, base.y * 0.8, col_height * 0.7),
        Base.Vector(base.x * 0.5, base.y * 0.5, col_height)
    ]
    
    # Create the bezier curve for the column
    column_curve = make_bezier_curve(control_points)
    lines.append(column_curve)
    
    # Store the top point of the column
    column_tops.append(control_points[-1])

# Create upper structure (artistic central element)
# Central point slightly above the highest column
central_top = Base.Vector(0, 0, height * 1.1)

# Connect the column tops to the central point with curved beams
for top in column_tops:
    # Create control points for curved connection
    control_points = [
        top,
        Base.Vector(top.x * 0.6, top.y * 0.6, top.z + 0.5),
        Base.Vector(central_top.x, central_top.y, central_top.z - 0.5),
        central_top
    ]
    
    # Create the bezier curve
    curve = make_bezier_curve(control_points)
    lines.append(curve)

# Add some decorative elements (antenna-like extensions from the central point)
for i in range(3):
    angle = i * (2 * math.pi / 3) + math.pi/6
    end_point = Base.Vector(
        math.cos(angle) * 1.0,
        math.sin(angle) * 1.0,
        central_top.z + 1.5 + i * 0.5
    )
    
    # Create a curved extension
    control_points = [
        central_top,
        Base.Vector(
            central_top.x + math.cos(angle) * 0.3,
            central_top.y + math.sin(angle) * 0.3,
            central_top.z + 0.7
        ),
        Base.Vector(
            end_point.x - math.cos(angle) * 0.2,
            end_point.y - math.sin(angle) * 0.2,
            end_point.z - 0.3
        ),
        end_point
    ]
    
    curve = make_bezier_curve(control_points)
    lines.append(curve)
    
    # Add a small branch to each extension
    branch_angle = angle + math.pi/4
    branch_end = Base.Vector(
        end_point.x + math.cos(branch_angle) * 0.8,
        end_point.y + math.sin(branch_angle) * 0.8,
        end_point.z + 0.5
    )
    
    branch_control = [
        end_point,
        Base.Vector(
            end_point.x + math.cos(branch_angle) * 0.3,
            end_point.y + math.sin(branch_angle) * 0.3,
            end_point.z + 0.2
        ),
        branch_end
    ]
    
    branch_curve = make_bezier_curve(branch_control)
    lines.append(branch_curve)

# Add some diagonal bracing between columns for stability
for i in range(len(column_bases)):
    j = (i + 1) % len(column_bases)
    
    # Create control points for diagonal bracing
    mid_height = height * 0.4
    mid_point = Base.Vector(
        (column_bases[i].x + column_bases[j].x) / 2,
        (column_bases[i].y + column_bases[j].y) / 2,
        mid_height
    )
    
    # Brace from first column base to mid-height
    control_points1 = [
        column_bases[i],
        Base.Vector(
            column_bases[i].x * 0.8 + mid_point.x * 0.2,
            column_bases[i].y * 0.8 + mid_point.y * 0.2,
            mid_height * 0.3
        ),
        Base.Vector(
            column_bases[i].x * 0.3 + mid_point.x * 0.7,
            column_bases[i].y * 0.3 + mid_point.y * 0.7,
            mid_height * 0.7
        ),
        mid_point
    ]
    
    curve1 = make_bezier_curve(control_points1)
    lines.append(curve1)
    
    # Brace from mid-height to next column base
    control_points2 = [
        mid_point,
        Base.Vector(
            mid_point.x * 0.7 + column_bases[j].x * 0.3,
            mid_point.y * 0.7 + column_bases[j].y * 0.3,
            mid_height * 0.7
        ),
        Base.Vector(
            mid_point.x * 0.2 + column_bases[j].x * 0.8,
            mid_point.y * 0.2 + column_bases[j].y * 0.8,
            mid_height * 0.3
        ),
        column_bases[j]
    ]
    
    curve2 = make_bezier_curve(control_points2)
    lines.append(curve2)

# Add curved horizontal rings at different heights
ring_heights = [height * 0.3, height * 0.6, height * 0.8]
for h in ring_heights:
    radius = base_width/2 * (1 - h/height * 0.5)  # Radius decreases with height
    ring_points = []
    
    # Create points for the ring
    num_points = 12
    for i in range(num_points + 1):
        angle = i * 2 * math.pi / num_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        ring_points.append(Base.Vector(x, y, h))
    
    # Create bezier curve for a smoother ring
    ring_curve = Part.BSplineCurve()
    ring_curve.interpolate(ring_points)
    lines.append(ring_curve.toShape())
    
    # Connect ring to the nearest columns with some curved supports
    for col_base in column_bases:
        # Find the closest point on the ring to this column
        projected_angle = math.atan2(col_base.y, col_base.x)
        closest_x = radius * math.cos(projected_angle)
        closest_y = radius * math.sin(projected_angle)
        ring_point = Base.Vector(closest_x, closest_y, h)
        
        # Create a point on the column at this height
        col_height_ratio = h / height
        col_at_height = Base.Vector(
            col_base.x * (1 - col_height_ratio * 0.5),
            col_base.y * (1 - col_height_ratio * 0.5),
            h
        )
        
        # Create a curved support
        control_points = [
            ring_point,
            Base.Vector(
                (ring_point.x + col_at_height.x) / 2,
                (ring_point.y + col_at_height.y) / 2,
                h + 0.2
            ),
            col_at_height
        ]
        
        support_curve = make_bezier_curve(control_points, 10)
        lines.append(support_curve)

# Create a compound from all lines
artistic_structure = Part.makeCompound(lines)

# Create solid structure by giving thickness to the lines
solid_beams = []

for edge in artistic_structure.Edges:
    try:
        # For straight edges
        if isinstance(edge.Curve, Part.Line):
            circle = Part.makeCircle(beam_radius, edge.valueAt(0), edge.tangentAt(0))
            circle_face = Part.Face(Part.Wire(circle))
            beam = circle_face.extrude(edge.valueAt(edge.LastParameter) - edge.valueAt(0))
            solid_beams.append(beam)
        # For curved edges
        else:
            # Sample points along the curve
            num_samples = max(10, int(edge.Length / 0.5))  # Adjust based on length
            pipe_sections = []
            
            for i in range(num_samples):
                param = edge.FirstParameter + (edge.LastParameter - edge.FirstParameter) * i / (num_samples - 1)
                position = edge.valueAt(param)
                direction = edge.tangentAt(param)
                
                # Create a circle perpendicular to the curve
                circle = Part.makeCircle(beam_radius, position, direction)
                pipe_sections.append(circle)
            
            # Create a loft through all circles
            pipe_shape = Part.makeLoft(pipe_sections, True)
            solid_beams.append(pipe_shape)
    except Exception as e:
        print(f"Error creating beam: {e}")

# Use fuse operation only if there are beams to fuse
if solid_beams:
    try:
        structure_solid = solid_beams[0].multiFuse(solid_beams[1:])
        structure_obj = doc.addObject("Part::Feature", "ArtisticTruss")
        structure_obj.Shape = structure_solid
        doc.recompute()
    except Exception as e:
        print(f"Error fusing beams: {e}")
        
        # Alternative: add individual beams if fusion fails
        compound = Part.makeCompound(solid_beams)
        structure_obj = doc.addObject("Part::Feature", "ArtisticTruss")
        structure_obj.Shape = compound
        doc.recompute()
else:
    App.Console.PrintError("Error: No beams were created\n")

# Add a simple base plate
base_plate = Part.makeBox(base_width * 1.2, base_depth * 1.2, 0.1)
base_plate.translate(Base.Vector(-base_width * 0.6, -base_depth * 0.6, -0.1))
base_plate_obj = doc.addObject("Part::Feature", "BasePlate")
base_plate_obj.Shape = base_plate
doc.recompute()

# =========== Set up FEM analysis if needed ===========
# Create analysis
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
solver = ObjectsFem.makeSolverCalculixCcxTools(doc, "CalculiXCcxTools")
analysis.addObject(solver)

# Create a material (steel)
material = ObjectsFem.makeMaterialSolid(doc, "Material")
mat = material.Material
mat['Name'] = "Steel"
mat['YoungsModulus'] = "210000 MPa"
mat['PoissonRatio'] = "0.30"
mat['Density'] = "7900 kg/m^3"
material.Material = mat
material.References = [(structure_obj, "Solid")]
analysis.addObject(material)

# Create a mesh
mesh = doc.addObject('Fem::FemMeshShapeNetgenObject', "FEMMeshNetgen")
mesh.Shape = structure_obj.Shape
mesh.MaxSize = 0.2
mesh.MinSize = 0.01
mesh.SecondOrder = False
mesh.Optimize = True
mesh.Fineness = 2
mesh.GrowthRate = 1.5
doc.recompute()
analysis.addObject(mesh)

# Create fixed constraint at the base
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "FixedConstraint")
fixed_constraint.References = [(base_plate_obj, "Face1")]  # Bottom face of base plate
analysis.addObject(fixed_constraint)

# Create a force constraint at the top
force_constraint = ObjectsFem.makeConstraintForce(doc, "ForceConstraint")
force_constraint.References = [(structure_obj, "Vertex1")]  # This will need adjustment
force_constraint.Force = 1000.0  # 1kN force
force_constraint.Direction = (0.0, 0.0, -1.0)  # Z-direction downward
analysis.addObject(force_constraint)

print("Artistic truss structure created!")
print("The structure might be complex and challenging for FEM analysis.")
print("To run the analysis, execute the following in FreeCAD:")
print("1. Fem.ccxtools.FemToolsCcx.writeInputFile(solver)")
print("2. Fem.ccxtools.FemToolsCcx.run(solver)")
print("3. doc.recompute()")

# Save the document
doc.saveAs("/tmp/artistic_truss.FCStd") 