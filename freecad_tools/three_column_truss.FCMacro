import FreeCAD as App
import Part
import ObjectsFem
import Fem
from FreeCAD import Base
import math

# Open a new document
doc = App.newDocument("ThreeColumnTrussAnalysis")

# =========== Create a truss structure with three columns ===========
# Define dimensions
length = 6.0   # Length of the truss
width = 2.0    # Width between columns (front to back)
height = 1.5   # Height of the truss
segments = 6   # Number of segments along length
beam_radius = 0.05  # Thickness of beams

# Create a compound shape to hold all truss elements
lines = []

# Create the three rows of bottom points (for three columns)
bottom_front = []
bottom_middle = []
bottom_back = []

for i in range(segments + 1):
    x = i * (length / segments)
    bottom_front.append(Base.Vector(x, 0, 0))
    bottom_middle.append(Base.Vector(x, width/2, 0))
    bottom_back.append(Base.Vector(x, width, 0))

# Create the three rows of top points
top_front = []
top_middle = []
top_back = []

for i in range(segments + 1):
    x = i * (length / segments)
    top_front.append(Base.Vector(x, 0, height))
    top_middle.append(Base.Vector(x, width/2, height))
    top_back.append(Base.Vector(x, width, height))

# Function to create chord members (horizontal beams)
def create_chord_members(points):
    for i in range(segments):
        lines.append(Part.makePolygon([points[i], points[i+1]]))

# Function to create vertical members
def create_vertical_members(bottom_points, top_points):
    for i in range(segments + 1):
        lines.append(Part.makePolygon([bottom_points[i], top_points[i]]))

# Function to create diagonal members
def create_diagonal_members(bottom_points, top_points):
    for i in range(segments):
        lines.append(Part.makePolygon([bottom_points[i], top_points[i+1]]))
        lines.append(Part.makePolygon([top_points[i], bottom_points[i+1]]))

# Create horizontal chord members for all three columns
create_chord_members(bottom_front)
create_chord_members(bottom_middle)
create_chord_members(bottom_back)
create_chord_members(top_front)
create_chord_members(top_middle)
create_chord_members(top_back)

# Create vertical members for all three columns
create_vertical_members(bottom_front, top_front)
create_vertical_members(bottom_middle, top_middle)
create_vertical_members(bottom_back, top_back)

# Create diagonal members for all three columns
create_diagonal_members(bottom_front, top_front)
create_diagonal_members(bottom_middle, top_middle)
create_diagonal_members(bottom_back, top_back)

# Connect the columns with cross-bracing (front to middle, middle to back)
# Connect bottom points between columns
for i in range(segments + 1):
    # Connect front to middle
    lines.append(Part.makePolygon([bottom_front[i], bottom_middle[i]]))
    # Connect middle to back
    lines.append(Part.makePolygon([bottom_middle[i], bottom_back[i]]))
    
    # Connect top points between columns
    lines.append(Part.makePolygon([top_front[i], top_middle[i]]))
    lines.append(Part.makePolygon([top_middle[i], top_back[i]]))

# Add diagonal bracing between columns for additional stability
for i in range(segments):
    # Front to middle diagonal bracing
    lines.append(Part.makePolygon([bottom_front[i], bottom_middle[i+1]]))
    lines.append(Part.makePolygon([bottom_middle[i], bottom_front[i+1]]))
    lines.append(Part.makePolygon([top_front[i], top_middle[i+1]]))
    lines.append(Part.makePolygon([top_middle[i], top_front[i+1]]))
    
    # Middle to back diagonal bracing
    lines.append(Part.makePolygon([bottom_middle[i], bottom_back[i+1]]))
    lines.append(Part.makePolygon([bottom_back[i], bottom_middle[i+1]]))
    lines.append(Part.makePolygon([top_middle[i], top_back[i+1]]))
    lines.append(Part.makePolygon([top_back[i], top_middle[i+1]]))

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
    truss_obj = doc.addObject("Part::Feature", "ThreeColumnTruss")
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

# Create fixed constraint (at the six corners - two at each column)
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "FixedConstraint")
# Get the vertices at the bottom corners
corner_points = [
    bottom_front[0],          # Front first corner
    bottom_front[segments],   # Front last corner
    bottom_middle[0],         # Middle first corner
    bottom_middle[segments],  # Middle last corner
    bottom_back[0],           # Back first corner
    bottom_back[segments]     # Back last corner
]

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

# Create force constraints (vertical loads at top of each column)
# Middle column gets larger load
force_points = [
    top_front[int(segments/2)],    # Center of front top chord
    top_middle[int(segments/2)],   # Center of middle top chord
    top_back[int(segments/2)]      # Center of back top chord
]

force_values = [5000.0, 10000.0, 5000.0]  # 5kN on outer columns, 10kN on middle column

for idx, (point, force_val) in enumerate(zip(force_points, force_values)):
    force_constraint = ObjectsFem.makeConstraintForce(doc, f"ForceConstraint{idx+1}")
    
    force_vertex_name = None
    for i, vertex in enumerate(truss_obj.Shape.Vertexes):
        if (point - vertex.Point).Length < tolerance:
            force_vertex_name = f"Vertex{i+1}"
            break

    if force_vertex_name:
        force_constraint.References = [(truss_obj, force_vertex_name)]
        force_constraint.Force = force_val
        force_constraint.Direction = (0.0, 0.0, -1.0)  # Z-direction downward
        analysis.addObject(force_constraint)

# Run the analysis
doc.recompute()
solver.SolverType = "static"
solver.GeometricalNonlinearity = "linear"
solver.ThermoMechSteadyState = False
solver.MaterialNonlinearity = "none"
solver.IterationsControlParameterTimeUse = False

print("Three-column truss FEM analysis setup complete!")
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
doc.saveAs("/tmp/three_column_truss_analysis.FCStd") 