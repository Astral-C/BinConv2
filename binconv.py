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

use_bump = False
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
    elif(opt in ('-b', '--use_bump')):
        use_bump = True

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


nbt_data = []

try:
    batch_section = BatchManager(shapes, materials, use_bump)
    if(use_bump):
        nbt_data = BatchManager.CalculateTangentSpace(shapes, materials, attrib)
except ValueError as error:
    print(error)

textures = TextureManager(materials)
shaders = ShaderManager(materials, textures)

offsets = [0 for x in range(21)]

model = bStream(path=bin_pth)
model.writeUInt8(0x02)
model.writeString("NewBinModel")
model.writeUInt32List(offsets)

# Write each section independently 
position_section = bStream()
normal_section = bStream()
texcoord0_section = bStream()

for vertex in attrib.vertices:
    position_section.writeInt16(int(vertex))

if(use_bump):
    for normal in nbt_data:
        normal_section.writeFloat(normal)
else:
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
textures.writeTextures(model)
model.padTo32(model.tell())

offsets[1] = model.tell()
textures.writeMaterials(model)
model.padTo32(model.tell())

offsets[2] = model.tell()
model.write(position_section.read())
position_section.close()
model.padTo32(model.tell())

offsets[3] = model.tell()
model.write(normal_section.read())
normal_section.close()
model.padTo32(model.tell())

offsets[6] = model.tell()
model.write(texcoord0_section.read())
texcoord0_section.close()
model.padTo32(model.tell())

offsets[10] = model.tell()
shaders.writeShaders(model)
model.padTo32(model.tell())

offsets[11] = model.tell()
batch_section.write(model)
model.padTo32(model.tell())

offsets[12] = model.tell()
root.write(model, offsets[12])
model.padTo32(model.tell())

model.seek(0x0C)
model.writeUInt32List(offsets)
model.close()
print("Conversion Completed")