#!venv/bin/python3
import os, sys, getopt, tinyobjloader

#Just commandline options garbo
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:",["in=", "out="])
except getopt.GetoptError:
    print("binconv.py -i <objpath> -o <binpath>")
    sys.exit(2)

obj_pth = ''
bin_pth = ''

for opt, arg in opts:
    if(opt == '-h'):
        print("binconv.py -i <objpath> -o <binpath>")
        sys.exit()
    elif(opt in ('-i', '--in')):
        obj_pth = arg
    elif(opt in ('-o', '--out')):
        if(arg == ''):
            bin_pth = os.path.basename(obj_pth).replace('.obj','.bin')
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
attribs = obj.GetAttrib()
'''
Materials and Shapes will directly translate to batches and materials in bin
though doing a graph object per shape would be possible and might in the future be better
likely the best way to do things at the moment is to stick with a single graph object
with multiple parts
'''
materials = obj.GetMaterials()
shapes = obj.GetShapes()

for mat in materials:
    print(mat.name)
    print(mat.diffuse_texname)