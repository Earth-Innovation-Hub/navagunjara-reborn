import FreeCAD as App
import Part
import ObjectsFem
import Fem
from FreeCAD import Base
import math

# Open a new document
doc = App.newDocument("PyramidalTrussAnalysis")

# =========== Create a pyramidal truss structure directly in FreeCAD ===========
# Define dimensions
base_side_length = 4.0  # Length of each side of the triangular base
height = 3.0           # Height of the pyramid
beam_radius = 0.05     # Thickness of beams

# Create a compound shape to hold all truss elements
lines = []

# Define the triangular base vertices
base_points = []
for i in range(3):
    angle = i * 2 * math.pi / 3
    x = base_side_length * math.cos(angle)
    y = base_side_length * math.sin(angle)
    base_points.append(Base.Vector(x, y, 0))

# Create the base triangle edges
for i in range(3):
    lines.append(Part.makePolygon([base_points[i], base_points[(i+1)%3]]))

# Define the apex point
apex = Base.Vector(0, 0, height)

# Create edges from each base point to the apex
for i in range(3):
    lines.append(Part.makePolygon([base_points[i], apex]))

# Create horizontal reinforcement at 1/3 and 2/3 of the height
reinforcement_heights = [height/3, 2*height/3]

for h in reinforcement_heights:
    reinforcement_points = []
    # Create smaller triangles at different heights
    scale_factor = 1 - (h / height)
    
    for i in range(3):
        angle = i * 2 * math.pi / 3
        x = scale_factor * base_side_length * math.cos(angle)
        y = scale_factor * base_side_length * math.sin(angle)
        reinforcement_points.append(Base.Vector(x, y, h))
    
    # Create reinforcement triangles
    for i in range(3):
        lines.append(Part.makePolygon([reinforcement_points[i], reinforcement_points[(i+1)%3]]))
    
    # Connect reinforcement points to base and to each other
    if h == reinforcement_heights[0]:  # Only for the first reinforcement level
        for i in range(3):
            lines.append(Part.makePolygon([base_points[i], reinforcement_points[i]]))
    
    # Connect between reinforcement levels or to apex
    if h == reinforcement_heights[0]:  # First level connects to second level
        for i in range(3):
            next_level_point = Base.Vector(
                (1 - reinforcement_heights[1]/height) * base_side_length * math.cos(i * 2 * math.pi / 3),
                (1 - reinforcement_heights[1]/height) * base_side_length * math.sin(i * 2 * math.pi / 3),
                reinforcement_heights[1]
            )
            lines.append(Part.makePolygon([reinforcement_points[i], next_level_point]))
    else:  # Second level connects to apex
        for i in range(3):
            lines.append(Part.makePolygon([reinforcement_points[i], apex]))

    # Add diagonal reinforcements
    for i in range(3):
        if h == reinforcement_heights[0]:  # Diagonals between base and first level
            lines.append(Part.makePolygon([base_points[i], reinforcement_points[(i+1)%3]]))
        else:  # Diagonals between second level and apex
            prev_level_point = Base.Vector(
                (1 - reinforcement_heights[0]/height) * base_side_length * math.cos(i * 2 * math.pi / 3),
                (1 - reinforcement_heights[0]/height) * base_side_length * math.sin(i * 2 * math.pi / 3),
                reinforcement_heights[0]
            )
            lines.append(Part.makePolygon([prev_level_point, reinforcement_points[(i+1)%3]]))

# Create a compound from all lines
truss_structure = Part.makeCompound(lines)

# Create a solid truss by giving thickness to the line structure
solid_beams = []

for edge in truss_structure.Edges:
    circle = Part.makeCircle(beam_radius, edge.valueAt(0), edge.tangentAt(0))
    circle_face = Part.Face(Part.Wire(circle))
    beam = circle_face.extrude(edge.valueAt(edge.LastParameter) - edge.valueAt(0))
    solid_beams.append(beam)

# Use fuse operation only if there are beams to fuse
if solid_beams:
    truss_solid = solid_beams[0].multiFuse(solid_beams[1:])
    truss_obj = doc.addObject("Part::Feature", "PyramidalTruss")
    truss_obj.Shape = truss_solid
    doc.recompute()
else:
    App.Console.PrintError("Error: No beams were created\n")
    
# =========== Set up FEM analysis ===========
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
material.References = [(truss_obj, "Solid")]
analysis.addObject(material)

# Create a mesh
mesh = doc.addObject('Fem::FemMeshShapeNetgenObject', "FEMMeshNetgen")
mesh.Shape = truss_obj.Shape
mesh.MaxSize = 0.1
mesh.MinSize = 0.001
mesh.SecondOrder = False
mesh.Optimize = True
mesh.Fineness = 2
mesh.GrowthRate = 1.5
doc.recompute()
analysis.addObject(mesh)

# Create fixed constraint (at the base corners)
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "FixedConstraint")
# Get the vertices at the bottom corners
corner_points = base_points

# Find vertices closest to our known corner points
tolerance = 1e-5
fixed_vertex_names = []

for point in corner_points:
    for i, vertex in enumerate(truss_obj.Shape.Vertexes):
        if (point - vertex.Point).Length < tolerance:
            fixed_vertex_names.append(f"Vertex{i+1}")
            break

fixed_constraint.References = [(truss_obj, name) for name in fixed_vertex_names]
analysis.addObject(fixed_constraint)

# Create a force constraint (vertical load at apex)
force_constraint = ObjectsFem.makeConstraintForce(doc, "ForceConstraint")
# Find the apex vertex
force_vertex_name = None
for i, vertex in enumerate(truss_obj.Shape.Vertexes):
    if (apex - vertex.Point).Length < tolerance:
        force_vertex_name = f"Vertex{i+1}"
        break

if force_vertex_name:
    force_constraint.References = [(truss_obj, force_vertex_name)]
    force_constraint.Force = 5000.0  # 5kN downward force
    force_constraint.Direction = (0.0, 0.0, -1.0)  # Z-direction downward
    analysis.addObject(force_constraint)

# Run the analysis
doc.recompute()
solver.SolverType = "static"
solver.GeometricalNonlinearity = "linear"
solver.ThermoMechSteadyState = False
solver.MaterialNonlinearity = "none"
solver.IterationsControlParameterTimeUse = False

print("FEM analysis setup complete!")
print("To run the analysis, execute the following in FreeCAD:")
print("1. Fem.ccxtools.FemToolsCcx.writeInputFile(solver)")
print("2. Fem.ccxtools.FemToolsCcx.run(solver)")
print("3. doc.recompute()")
print("4. To view results, create a ResultMechanical object and link it to the mesh")

# Uncomment these lines to run the analysis automatically:
# Fem.ccxtools.FemToolsCcx.writeInputFile(solver)
# Fem.ccxtools.FemToolsCcx.run(solver)
# doc.recompute()
# result = ObjectsFem.makeResultMechanical(doc, 'Result')
# result.Mesh = mesh
# result.read()
# doc.recompute()

# Save the document
doc.saveAs("/tmp/pyramidal_truss_analysis.FCStd")