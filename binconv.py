#!venv/bin/python3
import os, sys, getopt, tinyobjloader
from scenegraph import GraphObject
from materials import ShaderManager, TextureManager
from geometry import BatchManager
from bStream import *

#Just commandline options garbo
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:",["in=", "out="])
except getopt.GetoptError:
    print("binconv.py -i <objpath> -o <binpath>")
    sys.exit(2)

obj_pth = ''
bin_pth = os.path.basename(obj_pth).replace('.obj','.bin')

for opt, arg in opts:
    if(opt == '-h'):
        print("binconv.py -i <objpath> -o <binpath>")
        sys.exit()
    elif(opt in ('-i', '--in')):
        obj_pth = arg
    elif(opt in ('-o', '--out')):
        bin_pth = arg

obj = tinyobjloader.ObjReader()
success = obj.ParseFromFile(obj_pth)

if(not success):
    print("Warning: ", obj.Warning())
    print("Error: ", obj.Error())
    print("Failed to Load Model {}".format(obj_pth))
    sys.exit(-1)

if(obj.Warning()):
    print("Warning: ", obj.Warning())

# Get all the verts, normals, and texcoords from the obj
attrib = obj.GetAttrib()
'''
Materials and Shapes will directly translate to batches and materials in bin
though doing a graph object per shape would be possible and might in the future be better
likely the best way to do things at the moment is to stick with a single graph object
with multiple parts
'''
materials = obj.GetMaterials()
shapes = obj.GetShapes()
root = GraphObject(shapes)
root.parts = [(x, shapes[x].mesh.material_ids[0]) for x in range(len(shapes))]

try:
    batch_section = BatchManager(shapes)
except ValueError as error:
    print(error)

shaders = ShaderManager(materials)
offsets = [0 for x in range(21)]

model = bStream(path=bin_pth)
model.writeUInt8(0x02)
model.writeString("NewBinModel")
model.writeUInt32List(offsets)

texture_section = TextureManager(shaders)

# Write each section independently 
position_section = bStream()
normal_section = bStream()
texcoord0_section = bStream()

for vertex in attrib.vertices:
    position_section.writeInt16(int(vertex))

for normal in attrib.normals:
    normal_section.writeFloat(normal)

c = 0
for coord in attrib.texcoords:
    if(c % 2 == 0):
        texcoord0_section.writeFloat(coord)
    else:    
        texcoord0_section.writeFloat(-coord)
    c += 1

position_section.seek(0)
normal_section.seek(0)
texcoord0_section.seek(0)

offsets[0] = model.tell()
texture_section.writeTextures(model)

offsets[1] = model.tell()
shaders.writeMaterials(model)

offsets[2] = model.tell()
model.write(position_section.read())
position_section.close()

offsets[3] = model.tell()
model.write(normal_section.read())
normal_section.close()

offsets[6] = model.tell()
model.write(texcoord0_section.read())
texcoord0_section.close()

offsets[10] = model.tell()
shaders.writeShaders(model)

offsets[11] = model.tell()
batch_section.write(model)

offsets[12] = model.tell()
root.write(model, offsets[12])
model.padTo32(model.tell())

model.seek(0x0C)
model.writeUInt32List(offsets)
model.close()
print("Conversion Completed")